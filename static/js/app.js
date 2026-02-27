/**
 * AI Hackathon Auto Apply Agent - Main Application
 */

class App {
    constructor() {
        this.currentPage = 'dashboard';
        this.user = null;
        this.init();
    }

    async init() {
        // Check authentication
        const token = localStorage.getItem('token');
        if (token) {
            try {
                const data = await api.getCurrentUser();
                this.user = data.user;
                this.showApp();
            } catch (e) {
                this.showLogin();
            }
        } else {
            this.showLogin();
        }

        this.setupEventListeners();
    }

    setupEventListeners() {
        // Auth tabs
        document.querySelectorAll('.auth-tab').forEach(tab => {
            tab.addEventListener('click', () => this.switchAuthTab(tab.dataset.tab));
        });

        // Login form
        document.getElementById('loginForm').addEventListener('submit', (e) => this.handleLogin(e));
        
        // Register form
        document.getElementById('registerForm').addEventListener('submit', (e) => this.handleRegister(e));

        // Logout button
        document.getElementById('logoutBtn').addEventListener('click', () => this.handleLogout());

        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => this.navigateTo(item.dataset.page));
        });

        // Page links
        document.querySelectorAll('[data-page]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigateTo(link.dataset.page);
            });
        });

        // Menu toggle
        document.getElementById('menuToggle').addEventListener('click', () => {
            document.querySelector('.sidebar').classList.toggle('open');
        });

        // Profile forms
        document.getElementById('profileForm').addEventListener('submit', (e) => this.handleProfileUpdate(e));
        document.getElementById('linksForm').addEventListener('submit', (e) => this.handleLinksUpdate(e));
        document.getElementById('resumeForm').addEventListener('submit', (e) => this.handleResumeUpload(e));
        document.getElementById('skillsForm').addEventListener('submit', (e) => this.handleSkillsUpdate(e));
        document.getElementById('preferencesForm').addEventListener('submit', (e) => this.handlePreferencesUpdate(e));

        // Settings forms
        document.getElementById('notificationSettingsForm').addEventListener('submit', (e) => this.handleNotificationSettings(e));
        document.getElementById('changePasswordForm').addEventListener('submit', (e) => this.handlePasswordChange(e));

        // Notification toggles
        document.getElementById('telegramNotifications').addEventListener('change', (e) => {
            document.getElementById('telegramConfig').classList.toggle('hidden', !e.target.checked);
        });
        document.getElementById('discordNotifications').addEventListener('change', (e) => {
            document.getElementById('discordConfig').classList.toggle('hidden', !e.target.checked);
        });

        // Test notification buttons
        document.getElementById('testEmailBtn').addEventListener('click', () => this.testNotification('email'));
        document.getElementById('testTelegramBtn').addEventListener('click', () => this.testNotification('telegram'));
        document.getElementById('testDiscordBtn').addEventListener('click', () => this.testNotification('discord'));

        // Quick action buttons
        document.getElementById('btnScrapeNow').addEventListener('click', () => this.scrapeHackathons());
        document.getElementById('btnAutoApplyAll').addEventListener('click', () => this.autoApplyEligible());
        document.getElementById('btnGenerateIdea').addEventListener('click', () => this.showIdeaGenerator());

        // Filters
        document.getElementById('filterSource').addEventListener('change', () => this.loadHackathons());
        document.getElementById('filterStatus').addEventListener('change', () => this.loadHackathons());
        document.getElementById('filterOnline').addEventListener('change', () => this.loadHackathons());
        document.getElementById('filterAppStatus').addEventListener('change', () => this.loadApplications());

        // Refresh button
        document.getElementById('btnRefreshHackathons').addEventListener('click', () => this.loadHackathons());

        // Mark all read
        document.getElementById('btnMarkAllRead').addEventListener('click', () => this.markAllNotificationsRead());

        // New idea button
        document.getElementById('btnNewIdea').addEventListener('click', () => this.showIdeaGenerator());

        // Modal close
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => this.closeModals());
        });

        // Global search
        document.getElementById('globalSearch').addEventListener('input', debounce((e) => {
            if (this.currentPage === 'hackathons') {
                this.loadHackathons({ search: e.target.value });
            }
        }, 300));
    }

    // Auth Methods
    switchAuthTab(tab) {
        document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
        document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
        
        document.getElementById('loginForm').classList.toggle('hidden', tab !== 'login');
        document.getElementById('registerForm').classList.toggle('hidden', tab !== 'register');
    }

    async handleLogin(e) {
        e.preventDefault();
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;

        try {
            const data = await api.login(email, password);
            this.user = data.user;
            this.showApp();
            this.showToast('Welcome back!', 'success');
        } catch (error) {
            document.getElementById('loginError').textContent = error.message;
        }
    }

    async handleRegister(e) {
        e.preventDefault();
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        if (password !== confirmPassword) {
            document.getElementById('registerError').textContent = 'Passwords do not match';
            return;
        }

        try {
            const data = await api.register(email, password);
            this.user = data.user;
            this.showApp();
            this.showToast('Account created successfully!', 'success');
        } catch (error) {
            document.getElementById('registerError').textContent = error.message;
        }
    }

    async handleLogout() {
        await api.logout();
        this.user = null;
        this.showLogin();
        this.showToast('Logged out successfully', 'info');
    }

    showLogin() {
        document.getElementById('loginModal').classList.add('active');
        document.getElementById('app').classList.add('hidden');
    }

    showApp() {
        document.getElementById('loginModal').classList.remove('active');
        document.getElementById('app').classList.remove('hidden');
        document.getElementById('userEmail').textContent = this.user?.email || '';
        this.loadDashboard();
        this.loadNotificationCount();
    }

    // Navigation
    navigateTo(page) {
        this.currentPage = page;
        
        // Update nav
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.page === page);
        });

        // Update pages
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.getElementById(`${page}Page`).classList.add('active');

        // Update title
        const titles = {
            'dashboard': 'Dashboard',
            'hackathons': 'Hackathons',
            'applications': 'My Applications',
            'ai-ideas': 'AI Generated Ideas',
            'profile': 'My Profile',
            'notifications': 'Notifications',
            'settings': 'Settings'
        };
        document.getElementById('pageTitle').textContent = titles[page] || 'Dashboard';

        // Load page data
        this.loadPageData(page);

        // Close sidebar on mobile
        document.querySelector('.sidebar').classList.remove('open');
    }

    loadPageData(page) {
        switch (page) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'hackathons':
                this.loadHackathons();
                break;
            case 'applications':
                this.loadApplications();
                break;
            case 'ai-ideas':
                this.loadAiIdeas();
                break;
            case 'profile':
                this.loadProfile();
                break;
            case 'notifications':
                this.loadNotifications();
                break;
            case 'settings':
                this.loadSettings();
                break;
        }
    }

    // Dashboard
    async loadDashboard() {
        try {
            // Load overview stats
            const overview = await api.getDashboardOverview();
            document.getElementById('totalHackathons').textContent = overview.hackathons?.total || 0;
            document.getElementById('upcomingHackathons').textContent = overview.hackathons?.upcoming || 0;
            document.getElementById('totalApplications').textContent = overview.applications?.total || 0;
            document.getElementById('aiIdeasCount').textContent = overview.ai_ideas || 0;

            // Update profile progress
            const completeness = overview.profile_completeness || 0;
            document.querySelector('.progress-circle').style.background = 
                `conic-gradient(var(--primary-color) ${completeness}%, var(--surface-light) ${completeness}%)`;
            document.querySelector('.progress-value').textContent = `${completeness}%`;

            // Load upcoming deadlines
            this.loadUpcomingDeadlines();

            // Load recent applications
            this.loadRecentApplications();

            // Load recommended hackathons
            this.loadRecommendedHackathons();

        } catch (error) {
            console.error('Error loading dashboard:', error);
            this.showToast('Error loading dashboard', 'error');
        }
    }

    async loadUpcomingDeadlines() {
        const container = document.getElementById('upcomingDeadlines');
        
        try {
            const data = await api.getUpcomingDeadlines(14, 5);
            
            if (!data.deadlines || data.deadlines.length === 0) {
                container.innerHTML = '<p class="text-center">No upcoming deadlines</p>';
                return;
            }

            container.innerHTML = data.deadlines.map(d => {
                const daysClass = d.days_left <= 3 ? 'urgent' : (d.days_left <= 7 ? 'soon' : 'normal');
                return `
                    <div class="deadline-item">
                        <div class="deadline-info">
                            <h4>${d.hackathon.name}</h4>
                            <span><i class="fas fa-calendar"></i> ${formatDate(d.hackathon.registration_deadline)}</span>
                        </div>
                        <span class="deadline-days ${daysClass}">${d.days_left} days</span>
                    </div>
                `;
            }).join('');

        } catch (error) {
            container.innerHTML = '<p class="text-center">Error loading deadlines</p>';
        }
    }

    async loadRecentApplications() {
        const container = document.getElementById('recentApplications');
        
        try {
            const data = await api.getRecentApplications(5);
            
            if (!data.applications || data.applications.length === 0) {
                container.innerHTML = '<p class="text-center">No applications yet</p>';
                return;
            }

            container.innerHTML = data.applications.map(a => `
                <div class="application-item">
                    <div>
                        <h4>${a.hackathon_name || 'Unknown'}</h4>
                        <span class="status-badge status-${a.status}">${a.status}</span>
                    </div>
                    <span>${formatDate(a.created_at)}</span>
                </div>
            `).join('');

        } catch (error) {
            container.innerHTML = '<p class="text-center">Error loading applications</p>';
        }
    }

    async loadRecommendedHackathons() {
        const container = document.getElementById('recommendedHackathons');
        
        try {
            const data = await api.getRecommendedHackathons(4);
            
            if (!data.hackathons || data.hackathons.length === 0) {
                container.innerHTML = '<p class="text-center">Complete your profile to get recommendations</p>';
                return;
            }

            container.innerHTML = `
                <div class="hackathons-grid">
                    ${data.hackathons.map(h => this.renderHackathonCard(h)).join('')}
                </div>
            `;

        } catch (error) {
            container.innerHTML = '<p class="text-center">Error loading recommendations</p>';
        }
    }

    // Hackathons
    async loadHackathons(extraParams = {}) {
        const container = document.getElementById('hackathonsList');
        container.innerHTML = '<div class="loading">Loading hackathons...</div>';

        const params = {
            source: document.getElementById('filterSource').value,
            status: document.getElementById('filterStatus').value,
            is_online: document.getElementById('filterOnline').value,
            ...extraParams
        };

        // Remove empty params
        Object.keys(params).forEach(key => {
            if (!params[key]) delete params[key];
        });

        try {
            const data = await api.getHackathons(params);
            
            if (!data.hackathons || data.hackathons.length === 0) {
                container.innerHTML = '<p class="text-center">No hackathons found</p>';
                return;
            }

            container.innerHTML = data.hackathons.map(h => this.renderHackathonCard(h)).join('');

            // Setup card click handlers
            container.querySelectorAll('.hackathon-card').forEach(card => {
                card.querySelector('.btn-details').addEventListener('click', () => {
                    this.showHackathonDetails(card.dataset.id);
                });
                card.querySelector('.btn-apply').addEventListener('click', () => {
                    this.applyToHackathon(card.dataset.id);
                });
            });

        } catch (error) {
            container.innerHTML = '<p class="text-center">Error loading hackathons</p>';
            this.showToast('Error loading hackathons', 'error');
        }
    }

    renderHackathonCard(h) {
        return `
            <div class="hackathon-card" data-id="${h.id}">
                <div class="hackathon-card-header">
                    <h4>${h.name}</h4>
                    <span class="hackathon-source">${h.source}</span>
                </div>
                <div class="hackathon-card-body">
                    <div class="hackathon-info">
                        <span><i class="fas fa-calendar"></i> ${h.registration_deadline ? formatDate(h.registration_deadline) : 'No deadline'}</span>
                        <span><i class="fas fa-map-marker-alt"></i> ${h.is_online ? 'Online' : (h.location || 'TBD')}</span>
                        ${h.prize_pool ? `<span><i class="fas fa-trophy"></i> ${h.prize_pool}</span>` : ''}
                    </div>
                    <div class="hackathon-tags">
                        ${(h.tags || []).slice(0, 3).map(t => `<span class="tag">${t}</span>`).join('')}
                    </div>
                </div>
                <div class="hackathon-card-footer">
                    <button class="btn btn-secondary btn-details">Details</button>
                    <button class="btn btn-primary btn-apply" ${!h.is_registration_open ? 'disabled' : ''}>
                        ${h.is_registration_open ? 'Apply' : 'Closed'}
                    </button>
                </div>
            </div>
        `;
    }

    async showHackathonDetails(id) {
        const modal = document.getElementById('hackathonModal');
        const container = document.getElementById('hackathonDetail');
        
        modal.classList.add('active');
        container.innerHTML = '<div class="loading">Loading...</div>';

        try {
            const h = await api.getHackathon(id);
            
            container.innerHTML = `
                <h2>${h.name}</h2>
                <p class="hackathon-source">${h.source}</p>
                
                <div class="detail-section">
                    <h3>Description</h3>
                    <p>${h.description || 'No description available'}</p>
                </div>

                <div class="detail-section">
                    <h3>Details</h3>
                    <ul>
                        <li><strong>Deadline:</strong> ${h.registration_deadline ? formatDate(h.registration_deadline) : 'Not specified'}</li>
                        <li><strong>Start Date:</strong> ${h.start_date ? formatDate(h.start_date) : 'Not specified'}</li>
                        <li><strong>Location:</strong> ${h.is_online ? 'Online' : (h.location || 'Not specified')}</li>
                        <li><strong>Organizer:</strong> ${h.organizer || 'Not specified'}</li>
                        <li><strong>Prize Pool:</strong> ${h.prize_pool || 'Not specified'}</li>
                        <li><strong>Team Size:</strong> ${h.min_team_size || 1} - ${h.max_team_size || 'Any'}</li>
                    </ul>
                </div>

                ${h.tags && h.tags.length ? `
                <div class="detail-section">
                    <h3>Tags</h3>
                    <div class="hackathon-tags">
                        ${h.tags.map(t => `<span class="tag">${t}</span>`).join('')}
                    </div>
                </div>
                ` : ''}

                <div class="detail-actions">
                    <a href="${h.url}" target="_blank" class="btn btn-secondary">
                        <i class="fas fa-external-link-alt"></i> View Original
                    </a>
                    <button class="btn btn-primary" onclick="app.checkEligibility(${h.id})">
                        <i class="fas fa-check-circle"></i> Check Eligibility
                    </button>
                    <button class="btn btn-primary" onclick="app.generateIdeaForHackathon(${h.id})">
                        <i class="fas fa-lightbulb"></i> Generate Idea
                    </button>
                    <button class="btn btn-success" onclick="app.applyToHackathon(${h.id})" ${!h.is_registration_open ? 'disabled' : ''}>
                        <i class="fas fa-paper-plane"></i> Apply Now
                    </button>
                </div>
            `;

        } catch (error) {
            container.innerHTML = '<p class="text-center">Error loading hackathon details</p>';
        }
    }

    async applyToHackathon(hackathonId) {
        try {
            const result = await api.applyToHackathon(hackathonId);
            this.showToast('Application created! Check My Applications.', 'success');
            this.closeModals();
        } catch (error) {
            if (error.message.includes('Already applied')) {
                this.showToast('You have already applied to this hackathon', 'warning');
            } else {
                this.showToast('Error creating application', 'error');
            }
        }
    }

    async checkEligibility(hackathonId) {
        try {
            this.showToast('Checking eligibility...', 'info');
            const result = await api.checkEligibility(hackathonId);
            
            const message = result.is_eligible 
                ? `✅ You are eligible! Score: ${Math.round(result.score * 100)}%`
                : `❌ Not eligible. Score: ${Math.round(result.score * 100)}%`;
            
            this.showToast(message, result.is_eligible ? 'success' : 'warning');
        } catch (error) {
            this.showToast('Error checking eligibility', 'error');
        }
    }

    // Applications
    async loadApplications() {
        const container = document.getElementById('applicationsList');
        container.innerHTML = '<tr><td colspan="5" class="loading">Loading...</td></tr>';

        const status = document.getElementById('filterAppStatus').value;
        const params = status ? { status } : {};

        try {
            const data = await api.getApplications(params);
            
            if (!data.applications || data.applications.length === 0) {
                container.innerHTML = '<tr><td colspan="5" class="text-center">No applications found</td></tr>';
                return;
            }

            container.innerHTML = data.applications.map(a => `
                <tr>
                    <td>${a.hackathon_name || 'Unknown'}</td>
                    <td><span class="status-badge status-${a.status}">${a.status}</span></td>
                    <td>${a.eligibility_score ? Math.round(a.eligibility_score * 100) + '%' : 'N/A'}</td>
                    <td>${a.applied_at ? formatDate(a.applied_at) : 'Not applied'}</td>
                    <td>
                        <button class="btn btn-secondary btn-sm" onclick="app.generateContent(${a.id})">
                            <i class="fas fa-magic"></i>
                        </button>
                        ${a.status === 'pending' ? `
                        <button class="btn btn-primary btn-sm" onclick="app.submitApplication(${a.id})">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                        ` : ''}
                    </td>
                </tr>
            `).join('');

        } catch (error) {
            container.innerHTML = '<tr><td colspan="5" class="text-center">Error loading applications</td></tr>';
        }
    }

    async generateContent(applicationId) {
        try {
            this.showToast('Generating AI content...', 'info');
            const result = await api.generateApplicationContent(applicationId);
            this.showToast('Content generated successfully!', 'success');
            this.loadApplications();
        } catch (error) {
            this.showToast('Error generating content', 'error');
        }
    }

    async submitApplication(applicationId) {
        try {
            this.showToast('Auto-applying...', 'info');
            const result = await api.autoApply(applicationId);
            this.showToast('Application submitted!', 'success');
            this.loadApplications();
        } catch (error) {
            this.showToast(error.message || 'Error submitting application', 'error');
        }
    }

    // AI Ideas
    async loadAiIdeas() {
        const container = document.getElementById('ideasList');
        container.innerHTML = '<div class="loading">Loading ideas...</div>';

        try {
            const data = await api.getGeneratedContent({ type: 'project_idea' });
            
            if (!data.content || data.content.length === 0) {
                container.innerHTML = '<p class="text-center">No AI ideas generated yet. Click "Generate New Idea" to get started!</p>';
                return;
            }

            container.innerHTML = data.content.map(idea => `
                <div class="idea-card">
                    <h4>${idea.project_name || idea.title || 'Project Idea'}</h4>
                    <p><strong>Problem:</strong> ${truncate(idea.problem_statement || '', 150)}</p>
                    <p><strong>Solution:</strong> ${truncate(idea.solution || idea.content, 150)}</p>
                    ${idea.tech_stack && idea.tech_stack.length ? `
                        <div class="hackathon-tags">
                            ${idea.tech_stack.map(t => `<span class="tag">${t}</span>`).join('')}
                        </div>
                    ` : ''}
                    <div class="idea-meta">
                        <span>Generated: ${formatDate(idea.created_at)}</span>
                        ${idea.user_rating ? `<span>Rating: ${'⭐'.repeat(idea.user_rating)}</span>` : ''}
                    </div>
                </div>
            `).join('');

        } catch (error) {
            container.innerHTML = '<p class="text-center">Error loading ideas</p>';
        }
    }

    async generateIdeaForHackathon(hackathonId) {
        try {
            this.showToast('Generating project idea...', 'info');
            const result = await api.generateProjectIdea(hackathonId);
            this.showToast('Idea generated! Check AI Ideas page.', 'success');
            this.closeModals();
        } catch (error) {
            this.showToast('Error generating idea', 'error');
        }
    }

    showIdeaGenerator() {
        this.showToast('Select a hackathon to generate an idea', 'info');
        this.navigateTo('hackathons');
    }

    // Profile
    async loadProfile() {
        try {
            const data = await api.getProfile();
            
            // Personal info
            document.getElementById('firstName').value = data.first_name || '';
            document.getElementById('lastName').value = data.last_name || '';
            document.getElementById('phone').value = data.phone || '';
            document.getElementById('country').value = data.country || '';
            document.getElementById('college').value = data.college || '';
            document.getElementById('degree').value = data.degree || '';
            document.getElementById('isStudent').checked = data.is_student || false;

            // Links
            document.getElementById('githubUrl').value = data.github_url || '';
            document.getElementById('linkedinUrl').value = data.linkedin_url || '';
            document.getElementById('portfolioUrl').value = data.portfolio_url || '';

            // Resume status
            const resumeStatus = document.getElementById('resumeStatus');
            if (data.resume_path) {
                resumeStatus.innerHTML = '<i class="fas fa-file-alt"></i><span>Resume uploaded</span>';
            } else {
                resumeStatus.innerHTML = '<i class="fas fa-file-alt"></i><span>No resume uploaded</span>';
            }

            // Skills
            document.getElementById('programmingLanguages').value = (data.programming_languages || []).join(', ');
            document.getElementById('frameworks').value = (data.frameworks || []).join(', ');
            document.getElementById('skills').value = (data.skills || []).join(', ');

            // Preferences
            document.getElementById('preferredTypes').value = (data.preferred_hackathon_types || []).join(', ');
            document.getElementById('bio').value = data.bio || '';
            document.getElementById('autoApplyEnabled').checked = data.auto_apply_enabled || false;

        } catch (error) {
            this.showToast('Error loading profile', 'error');
        }
    }

    async handleProfileUpdate(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);
        data.is_student = document.getElementById('isStudent').checked;

        try {
            await api.updateProfile(data);
            this.showToast('Profile updated!', 'success');
        } catch (error) {
            this.showToast('Error updating profile', 'error');
        }
    }

    async handleLinksUpdate(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);

        try {
            await api.updateProfile(data);
            this.showToast('Links updated!', 'success');
        } catch (error) {
            this.showToast('Error updating links', 'error');
        }
    }

    async handleResumeUpload(e) {
        e.preventDefault();
        const fileInput = document.getElementById('resumeFile');
        
        if (!fileInput.files.length) {
            this.showToast('Please select a file', 'warning');
            return;
        }

        const formData = new FormData();
        formData.append('resume', fileInput.files[0]);

        try {
            await api.uploadResume(formData);
            this.showToast('Resume uploaded and parsed!', 'success');
            this.loadProfile();
        } catch (error) {
            this.showToast('Error uploading resume', 'error');
        }
    }

    async handleSkillsUpdate(e) {
        e.preventDefault();
        const data = {
            programming_languages: document.getElementById('programmingLanguages').value.split(',').map(s => s.trim()).filter(s => s),
            frameworks: document.getElementById('frameworks').value.split(',').map(s => s.trim()).filter(s => s),
            skills: document.getElementById('skills').value.split(',').map(s => s.trim()).filter(s => s)
        };

        try {
            await api.updateSkills(data);
            this.showToast('Skills updated!', 'success');
        } catch (error) {
            this.showToast('Error updating skills', 'error');
        }
    }

    async handlePreferencesUpdate(e) {
        e.preventDefault();
        const data = {
            preferred_hackathon_types: document.getElementById('preferredTypes').value.split(',').map(s => s.trim()).filter(s => s),
            bio: document.getElementById('bio').value,
            auto_apply_enabled: document.getElementById('autoApplyEnabled').checked
        };

        try {
            await api.updateProfile(data);
            this.showToast('Preferences updated!', 'success');
        } catch (error) {
            this.showToast('Error updating preferences', 'error');
        }
    }

    // Notifications
    async loadNotifications() {
        const container = document.getElementById('notificationsList');
        container.innerHTML = '<div class="loading">Loading...</div>';

        try {
            const data = await api.getNotifications();
            
            if (!data.notifications || data.notifications.length === 0) {
                container.innerHTML = '<p class="text-center">No notifications</p>';
                return;
            }

            container.innerHTML = data.notifications.map(n => `
                <div class="notification-item ${n.is_read ? '' : 'unread'}">
                    <div class="notification-icon">
                        <i class="fas ${getNotificationIcon(n.type)}"></i>
                    </div>
                    <div class="notification-content">
                        <h4>${n.title}</h4>
                        <p>${n.message}</p>
                    </div>
                    <span class="notification-time">${formatDate(n.created_at)}</span>
                </div>
            `).join('');

        } catch (error) {
            container.innerHTML = '<p class="text-center">Error loading notifications</p>';
        }
    }

    async loadNotificationCount() {
        try {
            const data = await api.getUnreadCount();
            const badge = document.getElementById('notifBadge');
            
            if (data.unread_count > 0) {
                badge.textContent = data.unread_count;
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        } catch (error) {
            console.error('Error loading notification count:', error);
        }
    }

    async markAllNotificationsRead() {
        try {
            await api.markAllAsRead();
            this.loadNotifications();
            this.loadNotificationCount();
            this.showToast('All notifications marked as read', 'success');
        } catch (error) {
            this.showToast('Error marking notifications', 'error');
        }
    }

    // Settings
    async loadSettings() {
        try {
            const prefs = await api.getNotificationPreferences();
            
            document.getElementById('emailNotifications').checked = prefs.email_notifications || false;
            document.getElementById('telegramNotifications').checked = prefs.telegram_notifications || false;
            document.getElementById('discordNotifications').checked = prefs.discord_notifications || false;
            document.getElementById('telegramChatId').value = prefs.telegram_chat_id || '';
            document.getElementById('discordWebhook').value = prefs.discord_webhook || '';

            // Show/hide config sections
            document.getElementById('telegramConfig').classList.toggle('hidden', !prefs.telegram_notifications);
            document.getElementById('discordConfig').classList.toggle('hidden', !prefs.discord_notifications);

        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }

    async handleNotificationSettings(e) {
        e.preventDefault();
        const data = {
            email_notifications: document.getElementById('emailNotifications').checked,
            telegram_notifications: document.getElementById('telegramNotifications').checked,
            discord_notifications: document.getElementById('discordNotifications').checked,
            telegram_chat_id: document.getElementById('telegramChatId').value,
            discord_webhook: document.getElementById('discordWebhook').value
        };

        try {
            await api.updateNotificationPreferences(data);
            this.showToast('Settings saved!', 'success');
        } catch (error) {
            this.showToast('Error saving settings', 'error');
        }
    }

    async handlePasswordChange(e) {
        e.preventDefault();
        const currentPassword = document.getElementById('currentPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmNewPassword = document.getElementById('confirmNewPassword').value;

        if (newPassword !== confirmNewPassword) {
            this.showToast('Passwords do not match', 'warning');
            return;
        }

        try {
            await api.changePassword(currentPassword, newPassword);
            this.showToast('Password changed successfully!', 'success');
            e.target.reset();
        } catch (error) {
            this.showToast(error.message || 'Error changing password', 'error');
        }
    }

    async testNotification(channel) {
        try {
            this.showToast(`Sending test ${channel} notification...`, 'info');
            await api.testNotification(channel);
            this.showToast(`Test notification sent!`, 'success');
        } catch (error) {
            this.showToast(`Error sending ${channel} notification`, 'error');
        }
    }

    // Quick Actions
    async scrapeHackathons() {
        try {
            this.showToast('Scraping hackathons...', 'info');
            const result = await api.triggerScrape();
            this.showToast(`Found ${result.results?.new || 0} new hackathons!`, 'success');
            this.loadHackathons();
        } catch (error) {
            this.showToast('Error scraping hackathons', 'error');
        }
    }

    async autoApplyEligible() {
        this.showToast('This feature requires eligible hackathons. Check individual hackathons to auto-apply.', 'info');
    }

    // Utilities
    closeModals() {
        document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <i class="fas ${getToastIcon(type)}"></i>
            <span>${message}</span>
        `;
        container.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
}

// Utility functions
function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function truncate(str, length) {
    if (!str) return '';
    return str.length > length ? str.substring(0, length) + '...' : str;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function getNotificationIcon(type) {
    const icons = {
        'new_hackathon': 'fa-trophy',
        'application_submitted': 'fa-paper-plane',
        'deadline_reminder': 'fa-clock',
        'eligibility_check': 'fa-check-circle',
        'system': 'fa-cog'
    };
    return icons[type] || 'fa-bell';
}

function getToastIcon(type) {
    const icons = {
        'success': 'fa-check-circle',
        'error': 'fa-times-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };
    return icons[type] || 'fa-info-circle';
}

// Initialize app
const app = new App();
