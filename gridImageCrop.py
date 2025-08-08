#@author
#Angathan N
#19/04/2025

import cv2
import os
import sys
from datetime import datetime
from screeninfo import get_monitors

# Grid config
grid_rows, grid_cols = 6, 6
MAX_DISPLAY_WIDTH = 1600
MAX_DISPLAY_HEIGHT = 900
input_folder = "input_images"
base_output_folder = "cropped_grids"

# Create a timestamped session folder
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
session_folder = os.path.join(base_output_folder, f"session_{timestamp}")
os.makedirs(session_folder, exist_ok=True)

# Subfolders for labels
label_colors = {"healthy": (0, 255, 0), "damaged": (0, 0, 255)}
for label in label_colors:
    os.makedirs(os.path.join(session_folder, label), exist_ok=True)

# Globals
selected_cells = {}  # {cell_index: label}
current_label = None
cell_coords = []
saved_crops = {"healthy": 0, "damaged": 0}

def draw_grid(image, img_name, img_index, total_images):
    global display_scale
    img_copy = image.copy()
    h, w = img_copy.shape[:2]

    max_w = MAX_DISPLAY_WIDTH
    max_h = MAX_DISPLAY_HEIGHT

    # Resize if image is larger than screen
    display_scale = 1.0
    if w > max_w or h > max_h:
        scale_w = max_w / w
        scale_h = max_h / h
        display_scale = min(scale_w, scale_h)
        img_copy = cv2.resize(img_copy, None, fx=display_scale, fy=display_scale)

    # Calculate cell coords based on original size
    cell_coords.clear()
    cell_h, cell_w = h // grid_rows, w // grid_cols
    count = 0

    # Instructions bar
    instructions = "[h] Healthy   [d] Damaged   [Click] Select/Toggle   [s] Save   [q] Skip   [x] Exit"
    image_info = f"Image {img_index + 1} of {total_images}  |  File: {img_name}"
    cv2.rectangle(img_copy, (0, 0), (img_copy.shape[1], 30), (50, 50, 50), -1)
    cv2.putText(img_copy, instructions, (10, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.putText(img_copy, image_info, (10, 45),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    for i in range(grid_rows):
        for j in range(grid_cols):
            x1, y1 = j * cell_w, i * cell_h
            x2, y2 = x1 + cell_w, y1 + cell_h
            cell_coords.append((x1, y1, x2, y2))  # in original scale

            # Draw scaled box
            sx1, sy1 = int(x1 * display_scale), int(y1 * display_scale)
            sx2, sy2 = int(x2 * display_scale), int(y2 * display_scale)

            if count in selected_cells:
                label = selected_cells[count]
                color = label_colors[label]
                cv2.rectangle(img_copy, (sx1, sy1), (sx2, sy2), color, 3)
                cv2.putText(img_copy, f"{count}", (sx1 + 5, sy1 + 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            else:
                cv2.rectangle(img_copy, (sx1, sy1), (sx2, sy2), (200, 200, 200), 1)
                cv2.putText(img_copy, f"{count}", (sx1 + 5, sy1 + 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
            count += 1

    return img_copy



def click_event(event, x, y, flags, param):
    global selected_cells, current_label
    if event == cv2.EVENT_LBUTTONDOWN and current_label:
        # Rescale click to original image size
        orig_x = int(x / display_scale)
        orig_y = int(y / display_scale)
        for idx, (x1, y1, x2, y2) in enumerate(cell_coords):
            if x1 <= orig_x <= x2 and y1 <= orig_y <= y2:
                if idx in selected_cells:
                    if selected_cells[idx] == current_label:
                        print(f"Deselected cell {idx}")
                        del selected_cells[idx]
                    else:
                        print(f"Updated label for cell {idx} to {current_label}")
                        selected_cells[idx] = current_label
                else:
                    selected_cells[idx] = current_label
                    print(f"Selected cell {idx} as {current_label}")
                break


def save_selected_cells(img, img_name):
    h, w = img.shape[:2]
    cell_h, cell_w = h // grid_rows, w // grid_cols
    for idx, label in selected_cells.items():
        i = idx // grid_cols
        j = idx % grid_cols
        x1, y1 = j * cell_w, i * cell_h
        x2, y2 = x1 + cell_w, y1 + cell_h
        cropped = img[y1:y2, x1:x2]
        cropped = img[y1:y2, x1:x2]
        save_path = os.path.join(session_folder, label, f"{img_name}_cell{idx}.jpg")
        cv2.imwrite(save_path, cropped, [cv2.IMWRITE_JPEG_QUALITY, 100])
        saved_crops[label] += 1

# Main image loop
image_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

cv2.namedWindow("Image Grid", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Image Grid", int(get_monitors()[0].width * 0.95), int(get_monitors()[0].height * 0.90))
cv2.setMouseCallback("Image Grid", click_event)

for index, file in enumerate(image_files):
    img_path = os.path.join(input_folder, file)
    img = cv2.imread(img_path)
    img_name = os.path.splitext(file)[0]

    selected_cells = {}
    current_label = None

    print(f"\nViewing: {file}")
    print("Instructions:")
    print("- Press 'h' for healthy, 'd' for damaged")
    print("- Click cells to toggle or reassign label")
    print("- Press 's' to save and go to next image")
    print("- Press 'q' to skip image without saving")
    print("- Press 'x' to save and exit the entire program\n")

    while True:
        display = draw_grid(img, file, index, len(image_files))
        cv2.imshow("Image Grid", display)
        key = cv2.waitKey(10) & 0xFF

        if key == ord('h'):
            current_label = 'healthy'
            print("Current label: healthy")
        elif key == ord('d'):
            current_label = 'damaged'
            print("Current label: damaged")
        elif key == ord('s'):
            save_selected_cells(img, img_name)
            print(f"Saved {len(selected_cells)} crops.")
            break
        elif key == ord('q'):
            print("Skipped image.")
            break
        elif key == ord('x'):
            save_selected_cells(img, img_name)
            print(f"Saved {len(selected_cells)} crops before exit.")
            cv2.waitKey(1)
            cv2.destroyAllWindows()
            print("Exited program. Crops saved to session folder.")
            sys.exit()

# Final clean-up at the end
cv2.waitKey(1)
cv2.destroyAllWindows()
