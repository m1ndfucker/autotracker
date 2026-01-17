#!/usr/bin/env python3
"""Standalone overlay selector script using Pygame."""
import sys
import json
import os

# Disable pygame welcome message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'


def main():
    result_file = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        import pygame
        import pygame.locals as pg_locals
        QUIT = pg_locals.QUIT
        KEYDOWN = pg_locals.KEYDOWN
        K_ESCAPE = pg_locals.K_ESCAPE
        MOUSEBUTTONDOWN = pg_locals.MOUSEBUTTONDOWN
        MOUSEMOTION = pg_locals.MOUSEMOTION
        MOUSEBUTTONUP = pg_locals.MOUSEBUTTONUP
        FULLSCREEN = pg_locals.FULLSCREEN
        NOFRAME = pg_locals.NOFRAME
        SRCALPHA = pg_locals.SRCALPHA
    except ImportError as e:
        print(f"[Overlay] Import error: {e}", file=sys.stderr)
        if result_file:
            with open(result_file, 'w') as f:
                json.dump({"cancelled": True, "error": str(e)}, f)
        sys.exit(1)

    result = {"cancelled": True, "region": None}
    sys.stderr.write("[Overlay] Starting...\n")
    sys.stderr.flush()

    try:
        sys.stderr.write("[Overlay] Calling pygame.init()...\n")
        sys.stderr.flush()
        pygame.init()
        sys.stderr.write("[Overlay] pygame.init() done\n")
        sys.stderr.flush()

        # Get display info
        info = pygame.display.Info()
        screen_width = info.current_w
        screen_height = info.current_h
        sys.stderr.write(f"[Overlay] Screen: {screen_width}x{screen_height}\n")
        sys.stderr.flush()

        # Take screenshot first
        sys.stderr.write("[Overlay] Taking screenshot...\n")
        sys.stderr.flush()

        import mss
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Primary monitor
            screenshot = sct.grab(monitor)
            # Convert to pygame surface
            screenshot_surface = pygame.image.frombuffer(
                screenshot.rgb, (screenshot.width, screenshot.height), 'RGB'
            )

        sys.stderr.write("[Overlay] Screenshot taken, creating window...\n")
        sys.stderr.flush()

        # Create fullscreen window
        screen = pygame.display.set_mode((screen_width, screen_height), FULLSCREEN | NOFRAME)
        pygame.display.set_caption("Select Region")

        # Colors
        RECT_COLOR = (68, 136, 255)  # Blue
        WHITE = (255, 255, 255)

        # State
        start_pos = None
        current_pos = None
        dragging = False
        running = True

        # Darken the screenshot slightly
        dark_overlay = pygame.Surface((screen_width, screen_height))
        dark_overlay.fill((0, 0, 0))
        dark_overlay.set_alpha(80)  # 30% darker

        clock = pygame.time.Clock()

        print("[Overlay] Starting event loop...", file=sys.stderr)

        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False

                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        result = {"cancelled": True, "region": None}
                        running = False

                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        start_pos = event.pos
                        current_pos = event.pos
                        dragging = True

                elif event.type == MOUSEMOTION:
                    if dragging:
                        current_pos = event.pos

                elif event.type == MOUSEBUTTONUP:
                    if event.button == 1 and dragging:
                        dragging = False
                        end_pos = event.pos

                        x1, y1 = start_pos
                        x2, y2 = end_pos

                        if x1 > x2:
                            x1, x2 = x2, x1
                        if y1 > y2:
                            y1, y2 = y2, y1

                        w, h = x2 - x1, y2 - y1

                        if w >= 10 and h >= 10:
                            result = {
                                "cancelled": False,
                                "region": {
                                    "x1": int(x1),
                                    "y1": int(y1),
                                    "x2": int(x2),
                                    "y2": int(y2)
                                }
                            }
                            print(f"[Overlay] Selected: {result['region']}", file=sys.stderr)
                            running = False
                        else:
                            start_pos = None
                            current_pos = None

            # Draw
            screen.blit(screenshot_surface, (0, 0))  # Screenshot as background
            screen.blit(dark_overlay, (0, 0))  # Slight darkening

            # Draw instruction box at top
            instruction_rect = pygame.Rect(screen_width // 2 - 200, 10, 400, 40)
            pygame.draw.rect(screen, (0, 0, 0), instruction_rect)
            pygame.draw.rect(screen, WHITE, instruction_rect, 2)
            # Crosshair as instruction indicator
            pygame.draw.line(screen, WHITE, (screen_width // 2 - 15, 30), (screen_width // 2 + 15, 30), 2)
            pygame.draw.line(screen, WHITE, (screen_width // 2, 15), (screen_width // 2, 45), 2)

            # Draw selection rectangle
            if start_pos and current_pos:
                x1, y1 = start_pos
                x2, y2 = current_pos

                min_x, max_x = min(x1, x2), max(x1, x2)
                min_y, max_y = min(y1, y2), max(y1, y2)
                w, h = max_x - min_x, max_y - min_y

                if w > 0 and h > 0:
                    # Semi-transparent fill
                    rect_surface = pygame.Surface((w, h), SRCALPHA)
                    rect_surface.fill((68, 136, 255, 60))
                    screen.blit(rect_surface, (min_x, min_y))

                    # Border
                    pygame.draw.rect(screen, RECT_COLOR, (min_x, min_y, w, h), 3)

                    # Corner markers instead of text
                    marker_len = 10
                    # Top-left
                    pygame.draw.line(screen, WHITE, (min_x, min_y), (min_x + marker_len, min_y), 2)
                    pygame.draw.line(screen, WHITE, (min_x, min_y), (min_x, min_y + marker_len), 2)
                    # Bottom-right
                    pygame.draw.line(screen, WHITE, (max_x, max_y), (max_x - marker_len, max_y), 2)
                    pygame.draw.line(screen, WHITE, (max_x, max_y), (max_x, max_y - marker_len), 2)

            pygame.display.flip()
            clock.tick(60)

    except Exception as e:
        print(f"[Overlay] Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        result = {"cancelled": True, "error": str(e)}

    finally:
        pygame.quit()

    print(f"[Overlay] Result: {result}", file=sys.stderr)

    # Write result
    if result_file:
        with open(result_file, 'w') as f:
            json.dump(result, f)
        print(f"[Overlay] Wrote to {result_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
