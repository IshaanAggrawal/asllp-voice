"""
Professional Registration Page with Comprehensive Validation
- Real-time password strength checking
- Email validation
- Username requirements
- Security best practices
"""

import streamlit as st
import re
import time
from utils.api import register_user

def check_password_strength(password):
    """Check password strength and return feedback"""
    strength = 0
    feedback = []
    
    if len(password) >= 8:
        strength += 1
    else:
        feedback.append("❌ At least 8 characters")
    
    if re.search(r"[a-z]", password):
        strength += 1
    else:
        feedback.append("❌ At least one lowercase letter")
    
    if re.search(r"[A-Z]", password):
        strength += 1
    else:
        feedback.append("❌ At least one uppercase letter")
    
    if re.search(r"\d", password):
        strength += 1
    else:
        feedback.append("❌ At least one number")
    
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        strength += 1
        feedback.append("✅ Special character included")
    
    return strength, feedback

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def show_register_page():
    """Professional registration page with validation"""
    st.markdown("""
    <div style='text-align: center; margin: 2rem 0 3rem 0;'>
        <div class='gradient-text'>📝 Create Account</div>
        <p style='color: var(--text-secondary); font-size: 1.1rem; margin-top: 0.5rem;'>
            Join the AI voice orchestration platform
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Security notice
    st.info("🔒 **Secure Registration**: Your password will be encrypted with industry-standard PBKDF2 hashing")
    
    with st.form("registration_form", clear_on_submit=False):
        st.subheader("Account Information")
        
        # Username
        username = st.text_input(
            "Username *",
            placeholder="Choose a unique username",
            help="Minimum 3 characters, alphanumeric only",
            max_chars=150
        )
        
        # Username validation feedback
        if username:
            if len(username) < 3:
                st.warning("⚠️ Username must be at least 3 characters")
            elif not re.match(r'^[a-zA-Z0-9_]+$', username):
                st.warning("⚠️ Username can only contain letters, numbers, and underscores")
            else:
                st.success("✅ Username format valid")
        
        # Email
        email = st.text_input(
            "Email Address *",
            placeholder="your.email@example.com",
            help="Valid email required for account recovery"
        )
        
        # Email validation feedback
        if email:
            if validate_email(email):
                st.success("✅ Email format valid")
            else:
                st.error("❌ Invalid email format")
        
        st.divider()
        st.subheader("Password Security")
        
        # Password
        password = st.text_input(
            "Password *",
            type="password",
            placeholder="Enter a strong password",
            help="Minimum 8 characters with mixed case, numbers, and symbols"
        )
        
        # Password strength meter
        if password:
            strength, feedback = check_password_strength(password)
            
            # Visual strength indicator
            strength_color = {
                0: "#EF4444",  # Red
                1: "#EF4444",
                2: "#F59E0B",  # Orange
                3: "#F59E0B",
                4: "#10B981",  # Green
                5: "#10B981"
            }
            
            strength_text = {
                0: "Very Weak",
                1: "Weak",
                2: "Fair",
                3: "Good",
                4: "Strong",
                5: "Very Strong"
            }
            
            st.markdown(f"""
            <div style='padding: 0.5rem; background: {strength_color[strength]}; color: white; border-radius: 4px; text-align: center; font-weight: 600;'>
                Password Strength: {strength_text[strength]} ({strength}/5)
            </div>
            """, unsafe_allow_html=True)
            
            # Feedback
            if feedback:
                st.markdown("**Requirements:**")
                for item in feedback:
                    st.markdown(f"- {item}")
        
        # Confirm password
        password_confirm = st.text_input(
            "Confirm Password *",
            type="password",
            placeholder="Re-enter your password"
        )
        
        # Password match check
        if password and password_confirm:
            if password == password_confirm:
                st.success("✅ Passwords match")
            else:
                st.error("❌ Passwords do not match")
        
        st.divider()
        
        # Terms checkbox
        terms_accepted = st.checkbox(
            "I agree to the terms of service and privacy policy",
            help="Required for account creation"
        )
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            submit = st.form_submit_button("📝 Create Account", type="primary", use_container_width=True)
        
        with col2:
            if st.form_submit_button("🔐 Login Instead", use_container_width=True):
                st.session_state.current_page = 'login'
                st.rerun()
        
        if submit:
            # Comprehensive validation
            errors = []
            
            if not username:
                errors.append("Username is required")
            elif len(username) < 3:
                errors.append("Username must be at least 3 characters")
            elif not re.match(r'^[a-zA-Z0-9_]+$', username):
                errors.append("Username can only contain letters, numbers, and underscores")
            
            if not email:
                errors.append("Email is required")
            elif not validate_email(email):
                errors.append("Invalid email format")
            
            if not password:
                errors.append("Password is required")
            elif len(password) < 8:
                errors.append("Password must be at least 8 characters")
            
            if password != password_confirm:
                errors.append("Passwords do not match")
            
            if not terms_accepted:
                errors.append("You must accept the terms of service")
            
            # Show errors
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Proceed with registration
                with st.spinner("🔄 Creating your account..."):
                    try:
                        result = register_user(username, email, password, password_confirm)
                        
                        if result.get('success'):
                            st.success("✅ Account created successfully!")
                            st.balloons()
                            user_data = result.get('data', {})
                            st.info(f"👤 Welcome, **{user_data.get('username', username)}**! Please login to continue.")
                            
                            time.sleep(2)
                            st.session_state.current_page = 'login'
                            st.rerun()
                        else:
                            st.error("❌ Registration failed. Please check the errors below:")
                            error_msg = result.get('error', 'Unknown error')
                            st.error(f"**Error**: {error_msg}")
                    
                    except Exception as e:
                        st.error(f"❌ Registration failed: {str(e)}")
                        st.info("💡 **Troubleshooting**: Ensure the backend server is running on port 8000")
    
    st.divider()
    
    # Security Features
    with st.expander("🔐 How We Protect Your Data"):
        st.markdown("""
        **Password Security:**
        - ✅ Encrypted with PBKDF2 algorithm (600,000 iterations)
        - ✅ Never stored in plain text
        - ✅ Salted with unique random string
        - ✅ Cannot be reversed or decrypted
        
        **Data Protection:**
        - ✅ All user data isolated by account
        - ✅ PostgreSQL database with row-level security
        - ✅ HTTPS encryption in production
        - ✅ CORS protection against unauthorized access
        
        **Compliance:**
        - ✅ GDPR-compliant data handling
        - ✅ Secure session management
        - ✅ Automatic logout after inactivity
        - ✅ Industry-standard JWT tokens
        """)
    
    # Interview Points
    with st.expander("💼 Technical Implementation (For Interviews)"):
        st.markdown("""
        **Frontend Validation (Streamlit):**
        ```python
        # 1. Real-time password strength checking
        # 2. Email format validation
        # 3. Username uniqueness (backend check)
        # 4. Password matching confirmation
        ```
        
        **Backend Validation (Django):**
        ```python
        # 1. UserRegistrationSerializer with custom validators
        # 2. Django password validators (4 built-in checks)
        # 3. Email uniqueness at database level
        # 4. PBKDF2 password hashing
        # 5. Atomic transaction for user creation
        ```
        
        **Security Architecture:**
        1. **Defense in Depth**: Frontend + backend validation
        2. **Principle of Least Privilege**: Users only access own data
        3. **Fail Secure**: Errors don't expose sensitive info
        4. **Audit Trail**: All account actions logged
        
        **Database Schema:**
        ```sql
        CREATE TABLE auth_user (
            id SERIAL PRIMARY KEY,
            username VARCHAR(150) UNIQUE NOT NULL,
            email VARCHAR(254) UNIQUE NOT NULL,
            password VARCHAR(128) NOT NULL,  -- Hashed
            date_joined TIMESTAMP NOT NULL
        );
        
        CREATE TABLE agents_agentconfiguration (
            id UUID PRIMARY KEY,
            user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
            -- Ensures user isolation via foreign key
        );
        ```
        """)
