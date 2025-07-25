import streamlit as st
from datetime import datetime
import requests

# ==== Prototype Backend Classes (in-memory) ====

class Bet:
    def __init__(self, user, text, event, odds, stake, status="pending"):
        self.user = user
        self.text = text
        self.event = event
        self.odds = odds
        self.stake = stake
        self.status = status
        self.timestamp = datetime.now()

    def __repr__(self):
        return (f"{self.user} bet '{self.text}' on {self.event} "
                f"@{self.odds} (Stake: {self.stake}, Status: {self.status}) "
                f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}]")

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.friends = []
        self.bets = []

    def add_friend(self, friend_username):
        if friend_username not in self.friends and friend_username != self.username:
            self.friends.append(friend_username)

    def post_bet(self, text, event, odds, stake):
        bet = Bet(self.username, text, event, odds, stake)
        self.bets.append(bet)
        return bet

class BetBud:
    def __init__(self):
        self.users = {}

    def register_user(self, username, password):
        if username in self.users:
            return False
        self.users[username] = User(username, password)
        return True

    def login_user(self, username, password):
        user = self.users.get(username)
        if user and user.password == password:
            return user
        return None

    def add_friend(self, username, friend_username):
        user = self.users.get(username)
        friend = self.users.get(friend_username)
        if not user or not friend:
            return False
        user.add_friend(friend_username)
        return True

    def post_bet(self, username, text, event, odds, stake):
        user = self.users.get(username)
        if not user:
            return None
        return user.post_bet(text, event, odds, stake)

    def get_feed(self, username):
        user = self.users.get(username)
        if not user:
            return []
        feed_bets = []
        for friend_username in user.friends:
            friend = self.users.get(friend_username)
            if friend:
                feed_bets.extend(friend.bets)
        feed_bets.sort(key=lambda bet: bet.timestamp, reverse=True)
        return feed_bets

# ======== Streamlit App ========

st.set_page_config(page_title="BetBud Prototype", layout="centered")
st.title("🏆 BetBud: Social Sports Betting Prototype")

if "app" not in st.session_state:
    st.session_state.app = BetBud()
if "user" not in st.session_state:
    st.session_state.user = None

app = st.session_state.app

# --- Registration/Login ---
with st.expander("Register / Login"):
    reg_col, log_col = st.columns(2)

    with reg_col:
        st.subheader("Register")
        reg_username = st.text_input("New Username", key="reg_user")
        reg_password = st.text_input("New Password", type="password", key="reg_pw")
        if st.button("Register"):
            if reg_username and reg_password:
                success = app.register_user(reg_username, reg_password)
                if success:
                    st.success(f"User '{reg_username}' registered. You can now log in.")
                else:
                    st.error("Username already taken.")

    with log_col:
        st.subheader("Login")
        log_username = st.text_input("Username", key="log_user")
        log_password = st.text_input("Password", type="password", key="log_pw")
        if st.button("Login"):
            user = app.login_user(log_username, log_password)
            if user:
                st.session_state.user = user
                st.success(f"Welcome, {log_username}!")
            else:
                st.error("Login failed.")

# --- Main App (after login) ---
if st.session_state.user:
    user = st.session_state.user
    st.header(f"Hello, {user.username}! 👋")

    # Add Friends
    st.subheader("Add / Follow Friends")
    available_users = [u for u in app.users if u != user.username and u not in user.friends]
    friend_to_add = st.selectbox("Select user to follow", [""] + available_users)
    if friend_to_add and st.button("Add Friend"):
        if app.add_friend(user.username, friend_to_add):
            st.success(f"Now following {friend_to_add}")
        else:
            st.error("Failed to add friend.")

    # Post Bet
    st.subheader("Post a Bet")
    bet_text = st.text_input("Bet Description", key="bet_text")
    bet_event = st.text_input("Event", key="bet_event")
    bet_odds = st.number_input("Odds", min_value=1.01, step=0.01, key="bet_odds")
    bet_stake = st.number_input("Stake (€)", min_value=1.0, step=1.0, key="bet_stake")
    if st.button("Post Bet"):
        if bet_text and bet_event:
            bet = app.post_bet(user.username, bet_text, bet_event, bet_odds, bet_stake)
            st.success(f"Bet posted: {bet}")
        else:
            st.error("Please fill in all fields.")

    # Feed
    st.subheader("Your Feed (Friends' Bets)")
    feed = app.get_feed(user.username)
    if feed:
        for bet in feed:
            st.info(str(bet))
    else:
        st.write("No bets to show yet! Add friends and wait for them to post.")

    # --- GitHub Integration ---
    st.header("🔗 Explore Sports Betting Projects on GitHub")
    github_query = st.text_input("Search GitHub for (e.g., 'sports betting')", "sports betting")
    if st.button("Search GitHub"):
        with st.spinner("Searching GitHub..."):
            r = requests.get(
                f"https://api.github.com/search/repositories",
                params={"q": github_query, "sort": "stars", "order": "desc", "per_page": 5}
            )
            if r.status_code == 200:
                results = r.json()["items"]
                for repo in results:
                    st.markdown(
                        f"- [{repo['full_name']}]({repo['html_url']}) (⭐ {repo['stargazers_count']})<br>"
                        f"  <i>{repo['description']}</i>",
                        unsafe_allow_html=True,
                    )
            else:
                st.error("Failed to fetch from GitHub. Try again later.")

else:
    st.info("Register and log in to start using BetBud!")

