const axios = require('axios');

class ParasiteAgent {
    constructor(config) {
        this.agentId = config.agentId;
        this.apiUrl = config.apiUrl || 'https://memory-parasite-protocol-api.koyeb.app/api';
        this.goal = config.goal || 'Build innovative Solana protocol';
        this.apiKey = null;
    }

    async register() {
        try {
            const resp = await axios.post(`${this.apiUrl}/register-agent`, {
                agentId: this.agentId,
                goal: this.goal
            });
            this.apiKey = resp.data.apiKey;
            console.log(`🧬 Parasite agent registered: ${this.agentId}`);
            return resp.data;
        } catch (err) {
            console.error('❌ Failed to register parasite agent:', err.message);
        }
    }

    async sendInfection(targetId, suggestion, reasoning) {
        try {
            const resp = await axios.post(`${this.apiUrl}/inject-infection`, {
                attackerId: this.agentId,
                targetId: targetId,
                suggestion: suggestion,
                reasoning: reasoning
            });
            console.log(`🦠 Infection sent to ${targetId}: ${resp.data.infectionId}`);
            return resp.data;
        } catch (err) {
            console.error('❌ Failed to send infection:', err.message);
        }
    }

    async respond(infectionId, decision, details = {}) {
        try {
            const resp = await axios.post(`${this.apiUrl}/respond-to-infection`, {
                infectionId: infectionId,
                decision: decision,
                ...details
            });
            console.log(`🧬 Decision reported for ${infectionId}: ${decision}`);
            return resp.data;
        } catch (err) {
            console.error('❌ Failed to respond to infection:', err.message);
        }
    }
}

module.exports = { ParasiteAgent };
