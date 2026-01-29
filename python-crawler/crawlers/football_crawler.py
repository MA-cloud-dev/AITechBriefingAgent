"""
足球数据爬虫
使用 football-data.org API 获取英超比分和排行榜
"""
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class FootballDataClient:
    """
    Football-Data.org API 客户端
    API文档: https://www.football-data.org/documentation/quickstart
    """
    
    BASE_URL = "https://api.football-data.org/v4"
    PREMIER_LEAGUE_ID = "PL"  # 英超代码
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "X-Auth-Token": api_key
        }
    
    def _request(self, endpoint: str) -> Optional[Dict]:
        """发送API请求"""
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"[Football API] 请求失败: {e}")
            return None
    
    def get_standings(self) -> Optional[Dict]:
        """
        获取英超积分榜
        返回: 球队排名、积分、胜负场次等
        """
        data = self._request(f"competitions/{self.PREMIER_LEAGUE_ID}/standings")
        if not data:
            return None
        
        try:
            standings = data.get("standings", [])
            if not standings:
                return None
            
            # 取总积分榜 (TOTAL)
            total_table = None
            for s in standings:
                if s.get("type") == "TOTAL":
                    total_table = s.get("table", [])
                    break
            
            if not total_table:
                total_table = standings[0].get("table", [])
            
            result = {
                "season": data.get("season", {}).get("currentMatchday"),
                "teams": []
            }
            
            for team in total_table[:10]:  # 只取前10名
                result["teams"].append({
                    "position": team.get("position"),
                    "name": team.get("team", {}).get("shortName") or team.get("team", {}).get("name"),
                    "played": team.get("playedGames"),
                    "won": team.get("won"),
                    "draw": team.get("draw"),
                    "lost": team.get("lost"),
                    "points": team.get("points"),
                    "goal_diff": team.get("goalDifference")
                })
            
            return result
            
        except Exception as e:
            print(f"[Football API] 解析积分榜失败: {e}")
            return None
    
    def get_recent_matches(self, days: int = 3) -> Optional[Dict]:
        """
        获取最近几天的英超比赛
        返回: 比赛日期、对阵双方、比分
        """
        # 获取过去几天到未来1天的比赛
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        date_to = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        data = self._request(
            f"competitions/{self.PREMIER_LEAGUE_ID}/matches"
            f"?dateFrom={date_from}&dateTo={date_to}"
        )
        
        if not data:
            return None
        
        try:
            matches = data.get("matches", [])
            result = {"matches": []}
            
            for match in matches:
                status = match.get("status")
                home = match.get("homeTeam", {})
                away = match.get("awayTeam", {})
                score = match.get("score", {}).get("fullTime", {})
                
                match_info = {
                    "date": match.get("utcDate", "")[:10],
                    "home_team": home.get("shortName") or home.get("name"),
                    "away_team": away.get("shortName") or away.get("name"),
                    "home_score": score.get("home"),
                    "away_score": score.get("away"),
                    "status": status  # FINISHED, SCHEDULED, LIVE, etc.
                }
                result["matches"].append(match_info)
            
            return result
            
        except Exception as e:
            print(f"[Football API] 解析比赛数据失败: {e}")
            return None


def get_football_summary(api_key: str) -> Dict[str, Any]:
    """
    获取足球数据汇总（积分榜 + 最近比赛）
    """
    client = FootballDataClient(api_key)
    
    result = {
        "standings": None,
        "matches": None
    }
    
    # 获取积分榜
    print("[Football] 正在获取英超积分榜...")
    standings = client.get_standings()
    if standings:
        result["standings"] = standings
        print(f"[Football] 获取积分榜成功，共 {len(standings['teams'])} 支球队")
    
    # 获取最近比赛
    print("[Football] 正在获取最近比赛...")
    matches = client.get_recent_matches(days=3)
    if matches:
        result["matches"] = matches
        finished = [m for m in matches["matches"] if m["status"] == "FINISHED"]
        print(f"[Football] 获取比赛成功，{len(finished)} 场已结束")
    
    return result


def format_football_markdown(data: Dict[str, Any]) -> str:
    """
    将足球数据格式化为Markdown
    """
    if not data.get("standings") and not data.get("matches"):
        return ""
    
    lines = []
    lines.append("\n---\n")
    lines.append("## ⚽ 英超快报\n")
    
    # 最近比赛结果
    if data.get("matches"):
        finished_matches = [
            m for m in data["matches"]["matches"] 
            if m["status"] == "FINISHED"
        ]
        
        if finished_matches:
            lines.append("### 📅 最近比赛\n")
            for match in finished_matches[:5]:  # 最多显示5场
                home = match["home_team"]
                away = match["away_team"]
                h_score = match["home_score"] or 0
                a_score = match["away_score"] or 0
                
                # 高亮赢家
                if h_score > a_score:
                    lines.append(f"- **{home}** {h_score} - {a_score} {away}\n")
                elif a_score > h_score:
                    lines.append(f"- {home} {h_score} - {a_score} **{away}**\n")
                else:
                    lines.append(f"- {home} {h_score} - {a_score} {away}\n")
            lines.append("\n")
    
    # 积分榜 (前6名)
    if data.get("standings"):
        teams = data["standings"]["teams"][:6]
        lines.append("### 🏆 积分榜 Top 6\n")
        lines.append("| # | 球队 | 场 | 胜 | 平 | 负 | 积分 |\n")
        lines.append("|---|------|----|----|----|----|------|\n")
        
        for team in teams:
            pos = team["position"]
            name = team["name"]
            played = team["played"]
            won = team["won"]
            draw = team["draw"]
            lost = team["lost"]
            points = team["points"]
            
            # 前4名加粗（欧冠区）
            if pos <= 4:
                lines.append(f"| **{pos}** | **{name}** | {played} | {won} | {draw} | {lost} | **{points}** |\n")
            else:
                lines.append(f"| {pos} | {name} | {played} | {won} | {draw} | {lost} | {points} |\n")
        
        lines.append("\n")
    
    return "".join(lines)


if __name__ == "__main__":
    # 测试 - 从环境变量读取 API Key
    import os
    API_KEY = os.getenv("FOOTBALL_API_KEY", "")
    if not API_KEY:
        print("错误: 请设置环境变量 FOOTBALL_API_KEY")
    else:
        data = get_football_summary(API_KEY)
        print("\n" + format_football_markdown(data))

