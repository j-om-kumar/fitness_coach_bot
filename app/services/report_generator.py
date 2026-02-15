"""Daily report generation with nutritional summary and graphs."""
import io
import warnings
from datetime import date
from typing import Optional, Dict, Any
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge
import numpy as np

# Suppress matplotlib font warnings for emojis
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

from app.db.db_service import get_user_by_telegram_id, get_or_create_daily_log
from app.db.db import SessionLocal, User, Meal
from sqlalchemy import select


async def get_daily_nutrition_summary(user: User, log_date: date) -> Dict[str, Any]:
    """
    Get nutritional summary for a user on a specific date.
    
    Args:
        user: User instance
        log_date: Date to get summary for
        
    Returns:
        Dictionary with nutritional totals and meal details
    """
    async with SessionLocal() as session:
        # Get daily log
        daily_log = await get_or_create_daily_log(session, user.id, log_date)
        
        # Get all meals for the day
        result = await session.execute(
            select(Meal).where(Meal.daily_log_id == daily_log.id)
        )
        meals = list(result.scalars().all())
        
        # Calculate totals
        totals = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fats': 0,
            'fiber': 0,
            'meal_count': len(meals)
        }
        
        meal_details = []
        
        for meal in meals:
            totals['calories'] += meal.calories_kcal or 0
            totals['protein'] += meal.protein_g or 0
            totals['carbs'] += meal.carbs_g or 0
            totals['fats'] += meal.fats_g or 0
            totals['fiber'] += meal.fiber_g or 0
            
            meal_details.append({
                'type': meal.meal_type,
                'description': meal.description,
                'calories': meal.calories_kcal or 0,
                'protein': meal.protein_g or 0,
                'carbs': meal.carbs_g or 0,
                'fats': meal.fats_g or 0,
                'fiber': meal.fiber_g or 0
            })
        
        return {
            'totals': totals,
            'meals': meal_details,
            'weight': float(daily_log.weight_kg) if daily_log.weight_kg else None,
            'steps': daily_log.steps
        }


def create_daily_report_image(summary: Dict[str, Any], user_name: str, report_date: date) -> io.BytesIO:
    """
    Create a beautiful daily report image with nutrition summary and graphs.
    
    Args:
        summary: Nutrition summary dictionary
        user_name: User's name
        report_date: Date of the report
        
    Returns:
        BytesIO object containing the PNG image
    """
    # Set style
    plt.style.use('dark_background')
    
    # Create figure with subplots
    fig = plt.figure(figsize=(12, 8), facecolor='#1a1a2e')
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    totals = summary['totals']
    meals = summary['meals']
    
    # Title (removed emoji to avoid font warnings)
    fig.suptitle(
        f"Daily Nutrition Report - {report_date.strftime('%B %d, %Y')}",
        fontsize=20,
        fontweight='bold',
        color='#00d4ff',
        y=0.98
    )
    
    # Subtitle with user name
    fig.text(
        0.5, 0.93,
        f"Coach Report for {user_name}",
        ha='center',
        fontsize=14,
        color='#ffffff',
        alpha=0.8
    )
    
    # === 1. Main Stats (Top Left) ===
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.axis('off')
    
    # Removed emojis to prevent font warnings
    stats_text = f"""
    Total Calories: {totals['calories']} kcal
    Protein: {totals['protein']} g
    Carbs: {totals['carbs']} g
    Fats: {totals['fats']} g
    Fiber: {totals['fiber']} g
    Meals Logged: {totals['meal_count']}
    """
    
    if summary['weight']:
        stats_text += f"\nWeight: {summary['weight']} kg"
    if summary['steps']:
        stats_text += f"\nSteps: {summary['steps']:,}"
    
    ax1.text(
        0.1, 0.5,
        stats_text.strip(),
        fontsize=13,
        verticalalignment='center',
        color='#ffffff',
        fontfamily='monospace',
        bbox=dict(boxstyle='round', facecolor='#16213e', alpha=0.8, edgecolor='#00d4ff', linewidth=2)
    )

    
    # === 2. Macros Pie Chart (Top Right) ===
    ax2 = fig.add_subplot(gs[0, 1])
    
    if totals['protein'] > 0 or totals['carbs'] > 0 or totals['fats'] > 0:
        # Calculate calories from macros
        protein_cal = totals['protein'] * 4
        carbs_cal = totals['carbs'] * 4
        fats_cal = totals['fats'] * 9
        
        sizes = [protein_cal, carbs_cal, fats_cal]
        labels = [f"Protein\n{totals['protein']}g", f"Carbs\n{totals['carbs']}g", f"Fats\n{totals['fats']}g"]
        colors = ['#ff6b6b', '#4ecdc4', '#ffe66d']
        explode = (0.05, 0.05, 0.05)
        
        wedges, texts, autotexts = ax2.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            explode=explode,
            textprops={'color': 'white', 'fontsize': 11, 'fontweight': 'bold'}
        )
        
        ax2.set_title('Macro Distribution', fontsize=14, color='#00d4ff', pad=10)
    else:
        ax2.text(0.5, 0.5, 'No macro data', ha='center', va='center', fontsize=12, color='#888888')
        ax2.set_title('Macro Distribution', fontsize=14, color='#00d4ff', pad=10)
    
    # === 3. Meals Bar Chart (Middle) ===
    ax3 = fig.add_subplot(gs[1, :])
    
    if meals:
        meal_types = [m['type'].replace('_', ' ').title() for m in meals]
        calories_per_meal = [m['calories'] for m in meals]
        
        bars = ax3.barh(meal_types, calories_per_meal, color='#00d4ff', alpha=0.8, edgecolor='#ffffff', linewidth=1.5)
        
        # Add value labels on bars
        for i, (bar, cal) in enumerate(zip(bars, calories_per_meal)):
            ax3.text(
                bar.get_width() + 20,
                bar.get_y() + bar.get_height()/2,
                f'{cal} kcal',
                va='center',
                fontsize=11,
                color='#ffffff',
                fontweight='bold'
            )
        
        ax3.set_xlabel('Calories (kcal)', fontsize=12, color='#ffffff')
        ax3.set_title('Calories per Meal', fontsize=14, color='#00d4ff', pad=10)
        ax3.grid(axis='x', alpha=0.3, linestyle='--')
        ax3.set_facecolor('#16213e')
        ax3.tick_params(colors='#ffffff')
    else:
        ax3.text(0.5, 0.5, 'No meals logged today', ha='center', va='center', fontsize=12, color='#888888', transform=ax3.transAxes)
        ax3.set_title('Calories per Meal', fontsize=14, color='#00d4ff', pad=10)
        ax3.set_facecolor('#16213e')
    
    # === 4. Meal Details Table (Bottom) ===
    ax4 = fig.add_subplot(gs[2, :])
    ax4.axis('off')
    
    if meals:
        table_data = []
        table_data.append(['Meal', 'Description', 'Cal', 'P', 'C', 'F', 'Fiber'])
        
        for meal in meals:
            row = [
                meal['type'].replace('_', ' ').title()[:10],
                (meal['description'] or 'N/A')[:25],
                str(meal['calories']),
                str(meal['protein']),
                str(meal['carbs']),
                str(meal['fats']),
                str(meal['fiber'])
            ]
            table_data.append(row)
        
        table = ax4.table(
            cellText=table_data,
            cellLoc='center',
            loc='center',
            bbox=[0, 0, 1, 1]
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        
        # Style header row
        for i in range(7):
            cell = table[(0, i)]
            cell.set_facecolor('#00d4ff')
            cell.set_text_props(weight='bold', color='#000000')
            cell.set_edgecolor('#ffffff')
            cell.set_linewidth(2)
        
        # Style data rows
        for i in range(1, len(table_data)):
            for j in range(7):
                cell = table[(i, j)]
                cell.set_facecolor('#16213e')
                cell.set_text_props(color='#ffffff')
                cell.set_edgecolor('#00d4ff')
                cell.set_alpha(0.8)
    else:
        ax4.text(
            0.5, 0.5,
            'No detailed meal data available',
            ha='center',
            va='center',
            fontsize=12,
            color='#888888'
        )
    
    # Add footer (removed emoji to prevent font warnings)
    fig.text(
        0.5, 0.02,
        '💪 Keep up the great work! Stay consistent with your nutrition goals.',
        ha='center',
        fontsize=11,
        color='#00d4ff',
        style='italic'
    )

    
    # Save to BytesIO
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    buf.seek(0)
    plt.close(fig)
    
    return buf


async def generate_daily_report(telegram_user_id: int, report_date: date = None) -> Optional[io.BytesIO]:
    """
    Generate daily report image for a user.
    
    Args:
        telegram_user_id: Telegram user ID
        report_date: Date for the report (defaults to today)
        
    Returns:
        BytesIO containing the report image, or None if user not found
    """
    if report_date is None:
        report_date = date.today()
    
    user = await get_user_by_telegram_id(telegram_user_id)
    if not user:
        return None
    
    summary = await get_daily_nutrition_summary(user, report_date)
    
    # Get user's first name (you might want to store this in the database)
    user_name = f"User #{user.telegram_user_id}"
    
    image_buffer = create_daily_report_image(summary, user_name, report_date)
    
    return image_buffer
