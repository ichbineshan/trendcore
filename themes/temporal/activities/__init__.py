"""Theme generation activities."""

from themes.temporal.activities.theme_activities import (
    # Phase 1 Research Activities
    gather_macro_trends_activity,
    gather_wgsn_trends_activity,
    gather_consumer_trends_activity,
    # Phase 1D + Phase 2 Activities
    generate_theme_briefs_activity,
    generate_single_theme_activity,
    # Status Update Activities
    update_themes_completed_activity,
    update_themes_failed_activity,
)

__all__ = [
    # Phase 1 Research
    "gather_macro_trends_activity",
    "gather_wgsn_trends_activity",
    "gather_consumer_trends_activity",
    # Theme Generation
    "generate_theme_briefs_activity",
    "generate_single_theme_activity",
    # Status Updates
    "update_themes_completed_activity",
    "update_themes_failed_activity",
]
