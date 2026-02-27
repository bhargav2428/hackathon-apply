/**
 * API Service - Handles all API calls to the backend
 */

const API_BASE = '/api';

class ApiService {
    constructor() {
        this.token = localStorage.getItem('token');
    }

    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('token', token);
    }

    clearToken() {
        this.token = null;
        localStorage.removeItem('token');
    }

    async request(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        const config = {
            headers: this.getHeaders(),
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    }

    // Auth endpoints
    async login(email, password) {
        const data = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        if (data.token) {
            this.setToken(data.token);
        }
        return data;
    }

    async register(email, password) {
        const data = await this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        if (data.token) {
            this.setToken(data.token);
        }
        return data;
    }

    async logout() {
        try {
            await this.request('/auth/logout', { method: 'POST' });
        } catch (e) {
            // Ignore errors on logout
        }
        this.clearToken();
    }

    async getCurrentUser() {
        return this.request('/auth/me');
    }

    async changePassword(currentPassword, newPassword) {
        return this.request('/auth/change-password', {
            method: 'POST',
            body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
        });
    }

    // Dashboard endpoints
    async getDashboardOverview() {
        return this.request('/dashboard/overview');
    }

    async getUpcomingDeadlines(days = 7, limit = 5) {
        return this.request(`/dashboard/upcoming-deadlines?days=${days}&limit=${limit}`);
    }

    async getRecentApplications(limit = 5) {
        return this.request(`/dashboard/recent-applications?limit=${limit}`);
    }

    async getRecommendedHackathons(limit = 5) {
        return this.request(`/dashboard/recommended-hackathons?limit=${limit}`);
    }

    async getActivityFeed(limit = 20) {
        return this.request(`/dashboard/activity-feed?limit=${limit}`);
    }

    async getAiIdeas(limit = 5) {
        return this.request(`/dashboard/ai-ideas?limit=${limit}`);
    }

    // Hackathons endpoints
    async getHackathons(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/hackathons/?${queryString}`);
    }

    async getHackathon(id) {
        return this.request(`/hackathons/${id}`);
    }

    async getUpcomingHackathons(limit = 10) {
        return this.request(`/hackathons/upcoming?limit=${limit}`);
    }

    async getHackathonSources() {
        return this.request('/hackathons/sources');
    }

    async getHackathonTags() {
        return this.request('/hackathons/tags');
    }

    async getHackathonStats() {
        return this.request('/hackathons/stats');
    }

    async triggerScrape(source = null) {
        return this.request('/hackathons/scrape', {
            method: 'POST',
            body: JSON.stringify({ source })
        });
    }

    async applyToHackathon(hackathonId) {
        return this.request(`/hackathons/${hackathonId}/apply`, {
            method: 'POST'
        });
    }

    // Applications endpoints
    async getApplications(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/applications/?${queryString}`);
    }

    async getApplication(id) {
        return this.request(`/applications/${id}`);
    }

    async updateApplication(id, data) {
        return this.request(`/applications/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async withdrawApplication(id) {
        return this.request(`/applications/${id}/withdraw`, {
            method: 'POST'
        });
    }

    async generateApplicationContent(id) {
        return this.request(`/applications/${id}/generate-content`, {
            method: 'POST'
        });
    }

    async autoApply(applicationId) {
        return this.request(`/applications/${applicationId}/auto-apply`, {
            method: 'POST'
        });
    }

    async bulkAutoApply(hackathonIds) {
        return this.request('/applications/bulk-apply', {
            method: 'POST',
            body: JSON.stringify({ hackathon_ids: hackathonIds })
        });
    }

    async getApplicationStats() {
        return this.request('/applications/stats');
    }

    // Profile endpoints
    async getProfile() {
        return this.request('/profile/');
    }

    async updateProfile(data) {
        return this.request('/profile/', {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async uploadResume(formData) {
        const url = `${API_BASE}/profile/resume`;
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`
            },
            body: formData
        });
        return response.json();
    }

    async deleteResume() {
        return this.request('/profile/resume', { method: 'DELETE' });
    }

    async getSkills() {
        return this.request('/profile/skills');
    }

    async updateSkills(data) {
        return this.request('/profile/skills', {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async getProfileCompleteness() {
        return this.request('/profile/completeness');
    }

    // AI endpoints
    async checkEligibility(hackathonId) {
        return this.request(`/ai/check-eligibility/${hackathonId}`);
    }

    async generateProjectIdea(hackathonId, context = '') {
        return this.request(`/ai/generate-project-idea/${hackathonId}`, {
            method: 'POST',
            body: JSON.stringify({ context })
        });
    }

    async generateMotivation(hackathonId, projectIdea = '') {
        return this.request(`/ai/generate-motivation/${hackathonId}`, {
            method: 'POST',
            body: JSON.stringify({ project_idea: projectIdea })
        });
    }

    async suggestTechStack(hackathonId) {
        return this.request(`/ai/suggest-tech-stack/${hackathonId}`);
    }

    async analyzeResume() {
        return this.request('/ai/analyze-resume', { method: 'POST' });
    }

    async skillGapAnalysis(hackathonId) {
        return this.request(`/ai/skill-gap-analysis/${hackathonId}`);
    }

    async predictSuccess(hackathonId) {
        return this.request(`/ai/predict-success/${hackathonId}`);
    }

    async getRecommendations(limit = 10) {
        return this.request(`/ai/recommendations?limit=${limit}`);
    }

    async getGeneratedContent(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/ai/generated-content?${queryString}`);
    }

    async rateContent(contentId, rating) {
        return this.request(`/ai/generated-content/${contentId}/rate`, {
            method: 'POST',
            body: JSON.stringify({ rating })
        });
    }

    // Notifications endpoints
    async getNotifications(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/notifications/?${queryString}`);
    }

    async getUnreadCount() {
        return this.request('/notifications/unread-count');
    }

    async markAsRead(notificationId) {
        return this.request(`/notifications/${notificationId}/read`, {
            method: 'POST'
        });
    }

    async markAllAsRead() {
        return this.request('/notifications/read-all', {
            method: 'POST'
        });
    }

    async deleteNotification(id) {
        return this.request(`/notifications/${id}`, {
            method: 'DELETE'
        });
    }

    async clearAllNotifications() {
        return this.request('/notifications/clear-all', {
            method: 'DELETE'
        });
    }

    async getNotificationPreferences() {
        return this.request('/notifications/preferences');
    }

    async updateNotificationPreferences(data) {
        return this.request('/notifications/preferences', {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async testNotification(channel) {
        return this.request('/notifications/test', {
            method: 'POST',
            body: JSON.stringify({ channel })
        });
    }
}

// Create global instance
const api = new ApiService();
