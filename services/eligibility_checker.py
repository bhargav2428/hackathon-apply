"""
Eligibility Checker Service - Determines if user is eligible for hackathons
"""
from typing import Dict, List, Any


class EligibilityChecker:
    """Service to check user eligibility for hackathons"""
    
    def check(self, hackathon, profile) -> Dict[str, Any]:
        """
        Check if a user is eligible for a hackathon
        
        Returns:
            Dict with:
                - is_eligible: bool
                - score: float (0.0 to 1.0)
                - reasons: List of eligibility factors
                - warnings: List of potential issues
        """
        if not profile:
            return {
                'is_eligible': False,
                'score': 0.0,
                'reasons': ['No profile found'],
                'warnings': ['Please complete your profile first']
            }
        
        score = 0.0
        max_score = 0.0
        reasons = []
        warnings = []
        
        # Check student requirement
        max_score += 1.0
        if hackathon.is_student_only:
            if profile.is_student:
                score += 1.0
                reasons.append('✓ Student status verified')
            else:
                reasons.append('✗ Hackathon is for students only')
                warnings.append('This hackathon requires student status')
        else:
            score += 1.0
            reasons.append('✓ No student requirement')
        
        # Check country eligibility
        max_score += 1.0
        eligible_countries = hackathon.eligible_countries or []
        if eligible_countries:
            if profile.country and profile.country.lower() in [c.lower() for c in eligible_countries]:
                score += 1.0
                reasons.append(f'✓ Country eligible: {profile.country}')
            elif profile.country:
                reasons.append(f'✗ Country not eligible: {profile.country}')
                warnings.append(f'This hackathon is limited to: {", ".join(eligible_countries[:5])}')
            else:
                score += 0.5  # Unknown, give partial score
                reasons.append('? Country not specified in profile')
                warnings.append('Please add your country to profile')
        else:
            score += 1.0
            reasons.append('✓ No country restrictions')
        
        # Check team size
        max_score += 1.0
        min_team = hackathon.min_team_size or 1
        max_team = hackathon.max_team_size or 10
        
        if min_team == 1:
            score += 1.0
            reasons.append('✓ Solo participation allowed')
        else:
            score += 0.7  # Partial, as user needs to form a team
            reasons.append(f'? Team of {min_team}-{max_team} required')
            warnings.append(f'You need to form a team of at least {min_team} members')
        
        # Check skills match
        max_score += 1.0
        required_skills = hackathon.required_skills or []
        if required_skills:
            user_skills = self._normalize_skills(profile)
            required_normalized = [s.lower() for s in required_skills]
            
            matching = sum(1 for s in user_skills if any(r in s or s in r for r in required_normalized))
            match_ratio = matching / len(required_skills) if required_skills else 1.0
            
            score += match_ratio
            
            if match_ratio >= 0.7:
                reasons.append(f'✓ Good skill match ({int(match_ratio * 100)}%)')
            elif match_ratio >= 0.4:
                reasons.append(f'? Partial skill match ({int(match_ratio * 100)}%)')
                warnings.append(f'Consider learning: {", ".join(required_skills[:3])}')
            else:
                reasons.append(f'✗ Low skill match ({int(match_ratio * 100)}%)')
                warnings.append(f'Required skills: {", ".join(required_skills[:5])}')
        else:
            score += 1.0
            reasons.append('✓ No specific skills required')
        
        # Check registration deadline
        max_score += 1.0
        if hackathon.is_registration_open:
            score += 1.0
            if hackathon.days_until_deadline is not None:
                reasons.append(f'✓ Registration open ({hackathon.days_until_deadline} days left)')
                if hackathon.days_until_deadline <= 3:
                    warnings.append('⚠️ Registration closing soon!')
            else:
                reasons.append('✓ Registration is open')
        else:
            reasons.append('✗ Registration is closed')
            warnings.append('Registration deadline has passed')
        
        # Check profile completeness
        max_score += 1.0
        completeness = self._calculate_profile_completeness(profile)
        score += completeness
        
        if completeness >= 0.8:
            reasons.append(f'✓ Profile is {int(completeness * 100)}% complete')
        else:
            reasons.append(f'? Profile is only {int(completeness * 100)}% complete')
            warnings.append('Complete your profile to improve eligibility')
        
        # Check hackathon preferences match
        max_score += 1.0
        if profile.preferred_hackathon_types:
            hackathon_tags = [t.lower() for t in (hackathon.tags or [])]
            hackathon_themes = [t.lower() for t in (hackathon.themes or [])]
            user_prefs = [p.lower() for p in profile.preferred_hackathon_types]
            
            if any(p in hackathon_tags or p in hackathon_themes for p in user_prefs):
                score += 1.0
                reasons.append('✓ Matches your hackathon preferences')
            else:
                score += 0.6
                reasons.append('? Does not match your stated preferences')
        else:
            score += 0.8
            reasons.append('? No hackathon preferences specified')
        
        # Calculate final score
        final_score = score / max_score if max_score > 0 else 0.0
        is_eligible = final_score >= 0.5 and hackathon.is_registration_open
        
        # Add overall assessment
        if final_score >= 0.8:
            reasons.insert(0, '🎯 Excellent match for this hackathon!')
        elif final_score >= 0.6:
            reasons.insert(0, '👍 Good candidate for this hackathon')
        elif final_score >= 0.4:
            reasons.insert(0, '⚠️ Possible fit, but some concerns')
        else:
            reasons.insert(0, '❌ May not be suitable for this hackathon')
        
        return {
            'is_eligible': is_eligible,
            'score': round(final_score, 2),
            'reasons': reasons,
            'warnings': warnings,
            'details': {
                'raw_score': round(score, 2),
                'max_score': round(max_score, 2),
                'student_check': hackathon.is_student_only,
                'country_check': bool(eligible_countries),
                'skill_check': bool(required_skills),
                'registration_open': hackathon.is_registration_open
            }
        }
    
    def _normalize_skills(self, profile) -> List[str]:
        """Normalize and combine all user skills"""
        skills = []
        
        if profile.skills:
            skills.extend([s.lower() for s in profile.skills])
        
        if profile.programming_languages:
            skills.extend([s.lower() for s in profile.programming_languages])
        
        if profile.frameworks:
            skills.extend([s.lower() for s in profile.frameworks])
        
        return skills
    
    def _calculate_profile_completeness(self, profile) -> float:
        """Calculate profile completeness as a ratio"""
        required_fields = [
            profile.first_name,
            profile.last_name,
            profile.country,
            profile.github_url,
            profile.college,
            profile.resume_path,
        ]
        
        important_fields = [
            profile.linkedin_url,
            profile.bio,
            profile.skills,
            profile.programming_languages,
        ]
        
        filled_required = sum(1 for f in required_fields if f)
        filled_important = sum(1 for f in important_fields if f and (not isinstance(f, list) or len(f) > 0))
        
        # Weight required fields more
        score = (filled_required * 2 + filled_important) / (len(required_fields) * 2 + len(important_fields))
        
        return min(1.0, score)
    
    def batch_check(self, hackathons: List, profile) -> List[Dict[str, Any]]:
        """Check eligibility for multiple hackathons"""
        results = []
        
        for hackathon in hackathons:
            result = self.check(hackathon, profile)
            result['hackathon_id'] = hackathon.id
            result['hackathon_name'] = hackathon.name
            results.append(result)
        
        # Sort by eligibility score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results
    
    def get_eligible_hackathons(self, hackathons: List, profile, min_score: float = 0.5) -> List:
        """Filter hackathons by eligibility"""
        results = self.batch_check(hackathons, profile)
        return [r for r in results if r['score'] >= min_score and r['is_eligible']]
