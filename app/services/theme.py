"""
Theme System Service

Manages storefront themes including Light, Dark, and Creator-brand color picker presets.
Provides theme validation, color utilities, and theme application functionality.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import re
import colorsys
from app.utils.exceptions import ValidationError


class ThemeType(str, Enum):
    """Available theme types."""
    LIGHT = "light"
    DARK = "dark"
    CREATOR_BRAND = "creator_brand"
    CUSTOM = "custom"


class ColorRole(str, Enum):
    """Color roles in a theme."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    ACCENT = "accent"
    BACKGROUND = "background"
    SURFACE = "surface"
    TEXT = "text"
    TEXT_SECONDARY = "text_secondary"
    BORDER = "border"
    ERROR = "error"
    SUCCESS = "success"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ColorPalette:
    """Represents a complete color palette for a theme."""
    primary: str
    secondary: str
    accent: str
    background: str
    surface: str
    text: str
    text_secondary: str
    border: str
    error: str = "#EF4444"
    success: str = "#10B981"
    warning: str = "#F59E0B"
    info: str = "#3B82F6"

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return asdict(self)

    def to_css_variables(self) -> str:
        """Convert to CSS custom properties."""
        css_vars = []
        for key, value in self.to_dict().items():
            css_vars.append(f"  --color-{key.replace('_', '-')}: {value};")
        return ":root {\n" + "\n".join(css_vars) + "\n}"


@dataclass 
class ThemeConfig:
    """Complete theme configuration."""
    name: str
    type: ThemeType
    colors: ColorPalette
    typography: Dict[str, Any]
    spacing: Dict[str, str]
    shadows: Dict[str, str]
    border_radius: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type.value,
            "colors": self.colors.to_dict(),
            "typography": self.typography,
            "spacing": self.spacing,
            "shadows": self.shadows,
            "border_radius": self.border_radius
        }


class ThemeService:
    """Service for managing storefront themes."""
    
    def __init__(self):
        """Initialize theme service with presets."""
        self._presets = self._initialize_presets()
    
    def _initialize_presets(self) -> Dict[str, ThemeConfig]:
        """Initialize built-in theme presets."""
        presets = {}
        
        # Light Theme
        presets["light"] = ThemeConfig(
            name="Light",
            type=ThemeType.LIGHT,
            colors=ColorPalette(
                primary="#3B82F6",
                secondary="#6B7280",
                accent="#8B5CF6",
                background="#FFFFFF",
                surface="#F9FAFB",
                text="#111827",
                text_secondary="#6B7280",
                border="#E5E7EB"
            ),
            typography={
                "font_family": "Inter, system-ui, -apple-system, sans-serif",
                "headings": {
                    "h1": {"size": "2.5rem", "weight": "700", "line_height": "1.2"},
                    "h2": {"size": "2rem", "weight": "600", "line_height": "1.3"},
                    "h3": {"size": "1.5rem", "weight": "600", "line_height": "1.4"}
                },
                "body": {"size": "1rem", "weight": "400", "line_height": "1.6"}
            },
            spacing={
                "xs": "0.25rem",
                "sm": "0.5rem", 
                "md": "1rem",
                "lg": "1.5rem",
                "xl": "2rem",
                "2xl": "3rem"
            },
            shadows={
                "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
                "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
                "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1)"
            },
            border_radius={
                "sm": "0.125rem",
                "md": "0.375rem", 
                "lg": "0.5rem",
                "xl": "0.75rem",
                "full": "9999px"
            }
        )
        
        # Dark Theme
        presets["dark"] = ThemeConfig(
            name="Dark",
            type=ThemeType.DARK,
            colors=ColorPalette(
                primary="#60A5FA",
                secondary="#9CA3AF",
                accent="#A78BFA",
                background="#111827",
                surface="#1F2937",
                text="#F9FAFB",
                text_secondary="#D1D5DB",
                border="#374151"
            ),
            typography={
                "font_family": "Inter, system-ui, -apple-system, sans-serif",
                "headings": {
                    "h1": {"size": "2.5rem", "weight": "700", "line_height": "1.2"},
                    "h2": {"size": "2rem", "weight": "600", "line_height": "1.3"},
                    "h3": {"size": "1.5rem", "weight": "600", "line_height": "1.4"}
                },
                "body": {"size": "1rem", "weight": "400", "line_height": "1.6"}
            },
            spacing={
                "xs": "0.25rem",
                "sm": "0.5rem",
                "md": "1rem", 
                "lg": "1.5rem",
                "xl": "2rem",
                "2xl": "3rem"
            },
            shadows={
                "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.3)",
                "md": "0 4px 6px -1px rgba(0, 0, 0, 0.4)",
                "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.4)",
                "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.4)"
            },
            border_radius={
                "sm": "0.125rem",
                "md": "0.375rem",
                "lg": "0.5rem", 
                "xl": "0.75rem",
                "full": "9999px"
            }
        )
        
        # Creator Brand Presets
        presets["vibrant"] = self._create_creator_preset(
            "Vibrant",
            primary="#FF6B6B", 
            secondary="#4ECDC4",
            accent="#FFE66D"
        )
        
        presets["professional"] = self._create_creator_preset(
            "Professional",
            primary="#2563EB",
            secondary="#64748B", 
            accent="#0EA5E9"
        )
        
        presets["creative"] = self._create_creator_preset(
            "Creative",
            primary="#8B5CF6",
            secondary="#EC4899",
            accent="#06B6D4"
        )
        
        presets["minimal"] = self._create_creator_preset(
            "Minimal",
            primary="#000000",
            secondary="#6B7280",
            accent="#F59E0B"
        )
        
        presets["warm"] = self._create_creator_preset(
            "Warm",
            primary="#DC2626",
            secondary="#EA580C",
            accent="#FBBF24"
        )
        
        presets["nature"] = self._create_creator_preset(
            "Nature",
            primary="#059669", 
            secondary="#0D9488",
            accent="#84CC16"
        )
        
        return presets
    
    def _create_creator_preset(self, name: str, primary: str, secondary: str, accent: str) -> ThemeConfig:
        """Create a creator brand preset with the given colors."""
        # Determine if this should be light or dark based on primary color brightness
        is_dark = self._is_color_dark(primary)
        
        if is_dark:
            background = "#111827"
            surface = "#1F2937"
            text = "#F9FAFB"
            text_secondary = "#D1D5DB"
            border = "#374151"
        else:
            background = "#FFFFFF"
            surface = "#F9FAFB"
            text = "#111827"
            text_secondary = "#6B7280"
            border = "#E5E7EB"
        
        return ThemeConfig(
            name=name,
            type=ThemeType.CREATOR_BRAND,
            colors=ColorPalette(
                primary=primary,
                secondary=secondary,
                accent=accent,
                background=background,
                surface=surface,
                text=text,
                text_secondary=text_secondary,
                border=border
            ),
            typography={
                "font_family": "Inter, system-ui, -apple-system, sans-serif",
                "headings": {
                    "h1": {"size": "2.5rem", "weight": "700", "line_height": "1.2"},
                    "h2": {"size": "2rem", "weight": "600", "line_height": "1.3"},
                    "h3": {"size": "1.5rem", "weight": "600", "line_height": "1.4"}
                },
                "body": {"size": "1rem", "weight": "400", "line_height": "1.6"}
            },
            spacing={
                "xs": "0.25rem",
                "sm": "0.5rem",
                "md": "1rem",
                "lg": "1.5rem", 
                "xl": "2rem",
                "2xl": "3rem"
            },
            shadows={
                "sm": f"0 1px 2px 0 {self._add_alpha(primary, 0.1)}",
                "md": f"0 4px 6px -1px {self._add_alpha(primary, 0.15)}",
                "lg": f"0 10px 15px -3px {self._add_alpha(primary, 0.15)}",
                "xl": f"0 20px 25px -5px {self._add_alpha(primary, 0.15)}"
            },
            border_radius={
                "sm": "0.125rem",
                "md": "0.375rem",
                "lg": "0.5rem",
                "xl": "0.75rem", 
                "full": "9999px"
            }
        )
    
    def get_preset(self, preset_name: str) -> Optional[ThemeConfig]:
        """Get a theme preset by name."""
        return self._presets.get(preset_name)
    
    def list_presets(self) -> List[Dict[str, Any]]:
        """List all available theme presets."""
        return [
            {
                "name": preset.name,
                "key": key,
                "type": preset.type.value,
                "preview_colors": {
                    "primary": preset.colors.primary,
                    "secondary": preset.colors.secondary,
                    "accent": preset.colors.accent,
                    "background": preset.colors.background
                }
            }
            for key, preset in self._presets.items()
        ]
    
    def create_custom_theme(self, name: str, colors: Dict[str, str]) -> ThemeConfig:
        """Create a custom theme from provided colors."""
        # Validate all required colors are provided
        required_colors = [
            "primary", "secondary", "accent", "background", 
            "surface", "text", "text_secondary", "border"
        ]
        
        for color_key in required_colors:
            if color_key not in colors:
                raise ValidationError(f"Required color '{color_key}' not provided")
            
            if not self.validate_hex_color(colors[color_key]):
                raise ValidationError(f"Invalid hex color for '{color_key}': {colors[color_key]}")
        
        # Create color palette
        palette = ColorPalette(**colors)
        
        # Determine theme type based on background brightness
        is_dark = self._is_color_dark(colors["background"])
        theme_type = ThemeType.DARK if is_dark else ThemeType.LIGHT
        
        return ThemeConfig(
            name=name,
            type=ThemeType.CUSTOM,
            colors=palette,
            typography={
                "font_family": "Inter, system-ui, -apple-system, sans-serif",
                "headings": {
                    "h1": {"size": "2.5rem", "weight": "700", "line_height": "1.2"},
                    "h2": {"size": "2rem", "weight": "600", "line_height": "1.3"},
                    "h3": {"size": "1.5rem", "weight": "600", "line_height": "1.4"}
                },
                "body": {"size": "1rem", "weight": "400", "line_height": "1.6"}
            },
            spacing={
                "xs": "0.25rem",
                "sm": "0.5rem",
                "md": "1rem",
                "lg": "1.5rem",
                "xl": "2rem", 
                "2xl": "3rem"
            },
            shadows={
                "sm": f"0 1px 2px 0 {self._add_alpha(colors['primary'], 0.1)}",
                "md": f"0 4px 6px -1px {self._add_alpha(colors['primary'], 0.15)}",
                "lg": f"0 10px 15px -3px {self._add_alpha(colors['primary'], 0.15)}",
                "xl": f"0 20px 25px -5px {self._add_alpha(colors['primary'], 0.15)}"
            },
            border_radius={
                "sm": "0.125rem",
                "md": "0.375rem",
                "lg": "0.5rem",
                "xl": "0.75rem",
                "full": "9999px"
            }
        )
    
    def validate_hex_color(self, color: str) -> bool:
        """Validate if a string is a valid hex color."""
        if not color or not isinstance(color, str):
            return False
        
        # Remove leading # if present
        color = color.lstrip('#')
        
        # Check if it's a valid hex color (3 or 6 characters)
        if len(color) not in [3, 6]:
            return False
        
        try:
            int(color, 16)
            return True
        except ValueError:
            return False
    
    def calculate_contrast_ratio(self, color1: str, color2: str) -> float:
        """Calculate contrast ratio between two colors."""
        def get_luminance(color: str) -> float:
            """Get relative luminance of a color."""
            # Convert hex to RGB
            color = color.lstrip('#')
            if len(color) == 3:
                color = ''.join([c*2 for c in color])
            
            r, g, b = [int(color[i:i+2], 16)/255.0 for i in (0, 2, 4)]
            
            # Apply gamma correction
            def gamma_correct(c):
                return c/12.92 if c <= 0.03928 else ((c + 0.055)/1.055) ** 2.4
            
            r, g, b = map(gamma_correct, [r, g, b])
            
            # Calculate luminance
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        lum1 = get_luminance(color1)
        lum2 = get_luminance(color2)
        
        # Ensure lighter color is in numerator
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        
        return (lighter + 0.05) / (darker + 0.05)
    
    def check_accessibility(self, theme: ThemeConfig) -> Dict[str, Any]:
        """Check theme accessibility compliance."""
        results = {
            "wcag_aa_compliant": True,
            "wcag_aaa_compliant": True,
            "issues": [],
            "suggestions": []
        }
        
        # Check text contrast ratios
        text_bg_ratio = self.calculate_contrast_ratio(
            theme.colors.text, 
            theme.colors.background
        )
        
        text_secondary_bg_ratio = self.calculate_contrast_ratio(
            theme.colors.text_secondary,
            theme.colors.background
        )
        
        # WCAG requirements: 4.5:1 for AA, 7:1 for AAA
        if text_bg_ratio < 4.5:
            results["wcag_aa_compliant"] = False
            results["issues"].append("Primary text contrast ratio too low")
        
        if text_bg_ratio < 7:
            results["wcag_aaa_compliant"] = False
        
        if text_secondary_bg_ratio < 3:
            results["issues"].append("Secondary text contrast ratio too low")
            results["suggestions"].append("Increase contrast for secondary text")
        
        # Check primary color contrast
        primary_bg_ratio = self.calculate_contrast_ratio(
            theme.colors.primary,
            theme.colors.background
        )
        
        if primary_bg_ratio < 3:
            results["suggestions"].append("Primary color may need more contrast with background")
        
        return results
    
    def generate_color_palette(self, base_color: str) -> Dict[str, str]:
        """Generate a harmonious color palette from a base color."""
        if not self.validate_hex_color(base_color):
            raise ValidationError(f"Invalid hex color: {base_color}")
        
        # Convert to HSL for manipulation
        rgb = self._hex_to_rgb(base_color)
        h, s, l = colorsys.rgb_to_hls(*[c/255.0 for c in rgb])
        
        # Generate complementary and triadic colors
        secondary_h = (h + 0.33) % 1.0  # 120 degrees
        accent_h = (h + 0.66) % 1.0     # 240 degrees
        
        # Generate palette
        palette = {
            "primary": base_color,
            "secondary": self._hsl_to_hex(secondary_h, s, l),
            "accent": self._hsl_to_hex(accent_h, s * 0.8, l),
            "background": "#FFFFFF" if l < 0.5 else "#111827",
            "surface": "#F9FAFB" if l < 0.5 else "#1F2937", 
            "text": "#111827" if l < 0.5 else "#F9FAFB",
            "text_secondary": "#6B7280" if l < 0.5 else "#D1D5DB",
            "border": "#E5E7EB" if l < 0.5 else "#374151"
        }
        
        return palette
    
    def _is_color_dark(self, color: str) -> bool:
        """Determine if a color is dark based on its luminance."""
        rgb = self._hex_to_rgb(color)
        # Calculate perceived brightness
        brightness = (rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000
        return brightness < 128
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _hsl_to_hex(self, h: float, s: float, l: float) -> str:
        """Convert HSL to hex color."""
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}".upper()
    
    def _add_alpha(self, hex_color: str, alpha: float) -> str:
        """Add alpha channel to hex color (convert to rgba)."""
        rgb = self._hex_to_rgb(hex_color)
        return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})" 