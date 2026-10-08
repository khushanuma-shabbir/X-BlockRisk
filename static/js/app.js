// Compact Fraud Detection Interface - Clean & User-Friendly

const app = {
    init() {
        this.setupEventListeners();
    },

    setupEventListeners() {
        const form = document.getElementById('checkForm');
        const input = document.getElementById('addressInput');
        
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const address = input.value.trim();
            this.checkAddress(address);
        });

        // Real-time validation
        input.addEventListener('input', (e) => {
            this.validateAddress(e.target.value);
        });
    },

    validateAddress(address) {
        const input = document.getElementById('addressInput');
        
        if (!address) {
            input.style.borderColor = '#E2E8F0';
            return;
        }

        const isValid = /^0x[a-fA-F0-9]{40}$/.test(address);
        input.style.borderColor = isValid ? '#4CAF50' : '#F44336';
    },

    async checkAddress(address) {
        // Validate
        if (!/^0x[a-fA-F0-9]{40}$/.test(address)) {
            this.showError('Invalid Ethereum address format. Must be 0x + 40 hex characters.');
            return;
        }

        // Show loading
        this.showLoading();
        this.hideError();
        this.hideResults();

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ address: address })
            });

            const data = await response.json();

            if (data.error) {
                this.showError(data.error);
                this.hideLoading();
                return;
            }

            this.hideLoading();
            this.displayResults(data);
        } catch (error) {
            this.hideLoading();
            this.showError('Error connecting to server. Please try again.');
            console.error('Error:', error);
        }
    },

    displayResults(data) {
        const resultsDiv = document.getElementById('results');
        const score = data.final_score || 0;
        const category = data.category || 'Unknown';
        
        // Show results
        resultsDiv.style.display = 'block';
        resultsDiv.classList.add('animate-in');

        // Update score
        document.getElementById('scoreValue').textContent = Math.round(score);
        
        // Update progress circle
        this.updateProgressRing(score);

        // Update risk badge with human-friendly text
        const badge = document.getElementById('riskBadge');
        badge.className = 'risk-badge';
        
        let badgeText = '';
        if (score >= 70) {
            badgeText = '⚠️ High Risk - Be Very Careful!';
            badge.classList.add('risk-high');
        } else if (score >= 50) {
            badgeText = '⚡ Medium Risk - Use Caution';
            badge.classList.add('risk-medium');
        } else if (score >= 33) {
            badgeText = '🔍 Moderate Risk - Be Aware';
            badge.classList.add('risk-medium');
        } else {
            badgeText = '✅ Low Risk - Looks Safe';
            badge.classList.add('risk-low');
        }
        badge.textContent = badgeText;

        // Display address
        document.getElementById('addressDisplay').textContent = data.address;

        // Display layers
        this.displayLayers(data);

        // Display explanations
        this.displayExplanations(data.explanations || []);

        // Smooth scroll
        setTimeout(() => {
            resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
    },

    displayLayers(data) {
        const container = document.getElementById('detectionLayers');
        
        const layers = [
            {
                name: 'AI Analysis',
                tooltip: 'Smart computer analysis of patterns',
                icon: '🤖',
                score: data.gnn_score || 0,
                confidence: data.gnn_confidence || 'N/A',
                humanScore: this.getHumanScore(data.gnn_score || 0)
            },
            {
                name: 'Behavior Check',
                tooltip: 'How this address behaves compared to known patterns',
                icon: '🧠',
                score: data.ml_score || 0,
                confidence: data.ml_confidence || 'N/A',
                humanScore: this.getHumanScore(data.ml_score || 0)
            },
            {
                name: 'Pattern Detection',
                tooltip: 'Looking for known fraud patterns',
                icon: '📊',
                score: data.rule_score || 0,
                confidence: 'ACTIVE',
                humanScore: this.getHumanScore(data.rule_score || 0)
            },
            {
                name: 'Fraud Database',
                tooltip: 'Checking against known scam addresses',
                icon: '🚨',
                score: data.blacklist_score || 0,
                confidence: data.is_blacklisted ? '⚠️ FOUND' : '✅ CLEAR',
                humanScore: data.is_blacklisted ? '⚠️ Listed' : '✅ Clean'
            }
        ];

        container.innerHTML = layers.map(layer => `
            <div class="layer-card" title="${layer.tooltip}">
                <div class="layer-header">
                    <div class="layer-name">
                        <span>${layer.icon}</span>
                        <span>${layer.name}</span>
                    </div>
                    <div class="layer-score">${Math.round(layer.score)}</div>
                </div>
                <div class="layer-confidence">${layer.humanScore || layer.confidence}</div>
            </div>
        `).join('');
    },

    getHumanScore(score) {
        if (score >= 80) return '🔴 Very Suspicious';
        if (score >= 60) return '🟠 Suspicious';
        if (score >= 40) return '🟡 Unusual';
        if (score >= 20) return '🟢 Mostly Normal';
        return '✅ Normal';
    },

    displayExplanations(explanations) {
        const container = document.getElementById('explanations');
        
        if (!explanations || explanations.length === 0) {
            container.innerHTML = '<div class="explanation-item">No detailed information available.</div>';
            return;
        }

        // Make explanations human-friendly
        const humanized = this.humanizeExplanations(explanations);

        container.innerHTML = humanized.map(exp => `
            <div class="explanation-item">${exp}</div>
        `).join('');
    },

    humanizeExplanations(explanations) {
        const humanFriendly = [];

        for (let exp of explanations) {
            let text = exp;

            // GNN explanations
            if (text.includes('GNN Model:') && text.includes('low confidence')) {
                humanFriendly.push('💡 Our AI model is still learning Ethereum patterns, so we\'re using other methods to check this address.');
            } else if (text.includes('GNN contributes minimal')) {
                continue; // Skip technical detail
            }

            // ML explanations
            else if (text.includes('Lightweight ML:')) {
                const score = text.match(/(\d+\.\d+)/)?.[0];
                if (score) {
                    const scoreNum = parseFloat(score);
                    if (scoreNum >= 70) {
                        humanFriendly.push(`⚠️ Our smart analysis detected suspicious behavior patterns (${Math.round(scoreNum)}% confidence this needs attention).`);
                    } else if (scoreNum >= 50) {
                        humanFriendly.push(`🔍 We found some unusual activity patterns. Not necessarily fraud, but worth being cautious.`);
                    } else {
                        humanFriendly.push(`✅ The transaction patterns look fairly normal based on our analysis.`);
                    }
                }
            } else if (text.includes('Trained on real Ethereum')) {
                continue; // Skip technical detail
            }

            // Rule-based
            else if (text.includes('Rule-Based:')) {
                const score = text.match(/(\d+\.\d+)/)?.[0];
                if (score && parseFloat(score) >= 70) {
                    humanFriendly.push('🚨 Warning: This address shows several red flags based on transaction patterns:');
                } else if (score && parseFloat(score) >= 30) {
                    humanFriendly.push('⚠️ Some suspicious patterns detected:');
                }
            }

            // Specific patterns - Make them human readable
            else if (text.includes('SCAM PATTERN')) {
                const ratio = text.match(/(\d+\.\d+)x/)?.[0];
                humanFriendly.push(`🚩 Red Flag: This address receives money but sends out ${ratio || 'much'} more - typical of scam addresses.`);
            }

            else if (text.includes('DISTRIBUTION') && text.includes('stolen fund')) {
                const count = text.match(/(\d+) addresses/)?.[1];
                humanFriendly.push(`🚩 Red Flag: Money is being distributed to ${count || 'many'} different addresses - often seen when stolen funds are being moved.`);
            }

            else if (text.includes('HIGH DISPERSION')) {
                humanFriendly.push(`🚩 Red Flag: This address collects money from few sources but spreads it to many destinations - suspicious behavior.`);
            }

            else if (text.includes('DRAINED')) {
                humanFriendly.push(`🚩 Red Flag: Large amounts were received but the balance is now empty - money was quickly moved out.`);
            }

            else if (text.includes('MICRO-SENDS')) {
                const count = text.match(/(\d+) sends/)?.[1];
                humanFriendly.push(`🚩 Red Flag: Made ${count || 'many'} tiny transfers - this pattern is used to distribute stolen funds.`);
            }

            else if (text.includes('QUICK FLIP')) {
                humanFriendly.push(`🚩 Red Flag: Money came in and was immediately sent out - hit-and-run pattern.`);
            }

            else if (text.includes('High volume with') && text.includes('imbalance')) {
                humanFriendly.push(`⚠️ Unusual: Very high transaction activity with unbalanced incoming vs outgoing transfers.`);
            }

            else if (text.includes('Wide distribution')) {
                const count = text.match(/(\d+) recipients/)?.[1];
                humanFriendly.push(`⚠️ Unusual: Sending to ${count || 'many'} different recipients - could be normal but worth noting.`);
            }

            // Blacklist
            else if (text.includes('BLACKLIST:')) {
                const reason = text.split('BLACKLIST:')[1]?.split('(')[0]?.trim();
                humanFriendly.push(`🚨 ALERT: This address is on the official fraud blacklist. Reason: ${reason || 'Verified scam'}`);
            }

            // Ensemble score
            else if (text.includes('Ensemble Score:')) {
                continue; // Skip, we show this in the badge
            }

            else if (text.includes('Detection layers:')) {
                continue; // Skip technical detail
            }

            // Admin control
            else if (text.includes('Admin-Control')) {
                continue; // Skip for now, too technical
            }

            // Default: clean up and show if meaningful
            else if (text.length > 10 && !text.includes('ℹ️')) {
                // Remove emojis and technical jargon
                let cleaned = text.replace(/[🚨⚠✅🤖🧠📊🔐🎯ℹ️]/g, '').trim();
                cleaned = cleaned.replace(/GNN|ML|Rule-Based:/g, '').trim();
                if (cleaned.length > 10) {
                    // Don't add if it's too technical
                    if (!cleaned.includes('weight') && !cleaned.includes('trained on')) {
                        humanFriendly.push(cleaned);
                    }
                }
            }
        }

        // Add summary if high risk
        if (humanFriendly.length > 3) {
            humanFriendly.unshift('📋 Summary: Multiple red flags detected. Please be very careful with this address.');
        }

        return humanFriendly.filter((item, index, self) => self.indexOf(item) === index); // Remove duplicates
    },

    updateProgressRing(score) {
        const circle = document.getElementById('progressCircle');
        const radius = 50;
        const circumference = radius * 2 * Math.PI;
        
        circle.style.strokeDasharray = `${circumference} ${circumference}`;
        circle.style.strokeDashoffset = circumference;

        const offset = circumference - (score / 100) * circumference;
        
        setTimeout(() => {
            circle.style.strokeDashoffset = offset;
        }, 100);

        // Change color based on risk
        const gradient = document.getElementById('gradient');
        if (score >= 70) {
            gradient.children[0].setAttribute('stop-color', '#F44336');
            gradient.children[1].setAttribute('stop-color', '#EF5350');
        } else if (score >= 33) {
            gradient.children[0].setAttribute('stop-color', '#FF9800');
            gradient.children[1].setAttribute('stop-color', '#FFB74D');
        } else {
            gradient.children[0].setAttribute('stop-color', '#4CAF50');
            gradient.children[1].setAttribute('stop-color', '#66BB6A');
        }
    },

    showLoading() {
        const btn = document.getElementById('checkBtn');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Analyzing...';
    },

    hideLoading() {
        const btn = document.getElementById('checkBtn');
        btn.disabled = false;
        btn.innerHTML = '🔍 Check If It\'s Safe';
    },

    showError(message) {
        this.hideError();
        const form = document.getElementById('checkForm');
        const errorDiv = document.createElement('div');
        errorDiv.id = 'errorMessage';
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `<span>⚠️</span> ${message}`;
        form.appendChild(errorDiv);
    },

    hideError() {
        const errorDiv = document.getElementById('errorMessage');
        if (errorDiv) errorDiv.remove();
    },

    hideResults() {
        const resultsDiv = document.getElementById('results');
        resultsDiv.style.display = 'none';
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
