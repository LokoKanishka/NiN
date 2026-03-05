require('dotenv').config();
const express = require('express');
const { spawn } = require('child_process');
const { SSEServerTransport } = require('@modelcontextprotocol/sdk/server/sse.js');
const path = require('path');

const mcpServers = [
    { id: 'github', name: 'GitHub', port: 13010, command: 'npx', args: ['-y', '@modelcontextprotocol/server-github'] },
    { id: 'figma', name: 'Figma', port: 13011, command: 'npx', args: ['-y', '@modelcontextprotocol/server-figma'] },
    { id: 'slack', name: 'Slack', port: 13012, command: 'npx', args: ['-y', '@modelcontextprotocol/server-slack'] },
    { id: 'sentry', name: 'Sentry', port: 13013, command: 'npx', args: ['-y', '@modelcontextprotocol/server-sentry'] },
    { id: 'playwright', name: 'Playwright', port: 13014, command: 'npx', args: ['-y', '@modelcontextprotocol/server-playwright'] },
    { id: 'context7', name: 'Context7', port: 13015, command: 'npx', args: ['-y', 'mcp-server-context7'] },
    { id: 'notion', name: 'Notion', port: 13016, command: 'npx', args: ['-y', '@notionhq/notion-mcp-server'] },
    { id: 'postgres', name: 'Postgres', port: 13017, command: 'npx', args: ['-y', '@modelcontextprotocol/server-postgres'] },
    { id: 'bigquery', name: 'BigQuery', port: 13018, command: 'npx', args: ['-y', '@modelcontextprotocol/server-bigquery'] },
    { id: 'n8n-v3', name: 'n8n V3', port: 13019, command: 'npx', args: ['-y', '@leonardsellem/n8n-mcp-server'] },
    { id: 'tavily', name: 'Tavily', port: 13020, command: 'npx', args: ['-y', '@modelcontextprotocol/server-tavily'], env: { TAVILY_API_KEY: process.env.TAVILY_API_KEY } },
    { id: 'system-health', name: 'System Health', port: 13021, command: 'npx', args: ['-y', '@modelcontextprotocol/server-system-health'] }
];

const targetId = process.env.MCP_ID;
const serversToLaunch = targetId ? mcpServers.filter(s => s.id === targetId) : mcpServers;

if (serversToLaunch.length === 0) {
    console.error(`❌ No se encontró configuración para MCP_ID: ${targetId}`);
    process.exit(1);
}

serversToLaunch.forEach(serverConfig => {
    const app = express();
    let sseTransport = null;

    console.log(`📡 [${serverConfig.name}] Iniciando proceso base: ${serverConfig.command} ${serverConfig.args.join(' ')}`);

    // El proceso solo se spawnea cuando alguien se conecta al SSE para ahorrar recursos
    let mcpProcess = null;

    const startMCP = () => {
        if (mcpProcess) return mcpProcess;

        mcpProcess = spawn(serverConfig.command, serverConfig.args, {
            env: { ...process.env, ...serverConfig.env }
        });

        mcpProcess.stderr.on('data', (data) => {
            console.error(`[${serverConfig.name} stderr]: ${data}`);
        });

        mcpProcess.on('close', (code) => {
            console.log(`[${serverConfig.name}] Proceso cerrado con código ${code}`);
            mcpProcess = null;
        });

        return mcpProcess;
    };

    app.get('/sse', async (req, res) => {
        console.log(`🚀 [${serverConfig.name}] Nueva conexión SSE en puerto ${serverConfig.port}`);
        sseTransport = new SSEServerTransport('/messages', res);

        const proc = startMCP();

        proc.stdout.on('data', (data) => {
            if (sseTransport) {
                // El SDK maneja el formateo SSE, pero aquí enviamos el streaming crudo si es necesario
                // En Bridge manual, el SDK es mejor.
            }
        });

        // El SDK maneja el transporte, solo necesitamos conectarlo.
        // Pero mcpProcess usa stdio. Necesitamos un bridge real stdio <-> SSE.
    });

    // REFACTOR: Usar el patrón de bridge SDK si es posible, o el manual de Taverna que funcionaba.
    // Volviendo al patrón manual probado en Taverna para asegurar compatibilidad.

    app.get('/sse', async (req, res) => {
        console.log(`🚀 [${serverConfig.name}] Conectando bridge SSE -> Stdio`);
        sseTransport = new SSEServerTransport('/messages', res);

        const proc = startMCP();

        // Conectar el transporte SSE con el proceso stdio
        await sseTransport.handleStart();

        // Este loop manual es el que Taverna usaba para puentear
        proc.stdout.on('data', (data) => {
            if (sseTransport) {
                // Notificar al transporte que hay datos del proceso
                // NOTA: SSEServerTransport del SDK espera objetos JSON de mcp-sdk
                // Si el server es un server MCP stdio estándar, emite JSON lines.
                const lines = data.toString().split('\n');
                lines.forEach(line => {
                    if (line.trim()) {
                        try {
                            const msg = JSON.parse(line);
                            sseTransport.send(msg);
                        } catch (e) {
                            // No es JSON válido o fragmento
                        }
                    }
                });
            }
        });
    });

    app.post('/messages', express.json(), async (req, res) => {
        const proc = startMCP();
        if (proc.stdin.writable) {
            proc.stdin.write(JSON.stringify(req.body) + '\n');
            res.status(200).send('OK');
        } else {
            res.status(500).send('MCP process stdin not writable');
        }
    });

    const port = process.env.PORT || serverConfig.port;
    app.listen(port, () => {
        console.log(`✅ [${serverConfig.name}] Bridge SSE activo en puerto ${port}`);
    });
});
