import csv
import time
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extract_graph_via_hover_firefox(output_csv_path):
    # 1. Configure standard Firefox options
    options = webdriver.FirefoxOptions()
    # (Optional) Uncomment the line below if you want it to run invisibly once you are logged in
    # options.add_argument('--headless')
    
    # 2. Initialize the Firefox Driver using GeckoDriverManager
    driver = webdriver.Firefox(
        service=Service(GeckoDriverManager().install()), 
        options=options
    )
    
    # Live URL to target
    live_url = "https://starlink.com/account/service-line/AST-2293597-46342-54?selectedDevice=ut01000000-00000000-0060d786&page=0&limit=5"
    
    try:
        # RESPECTING ROBOTS.TXT: Starlink requests a 'Crawl-delay: 10'. 
        # Waiting 10 seconds before navigating minimizes server load and avoids bot detection blocks.
        print("Respecting robots.txt rules... Pausing for 10 seconds before connection.")
        time.sleep(10)
        
        print(f"Navigating to live portal: {live_url}")
        driver.get(live_url)
        
        # USER MANIPULATION PAUSE: Since account dashboards are gated behind authentications,
        # the script safely stops here to let you fill out your email/password/MFA codes manually.
        print("\n" + "="*60)
        print("ACTION REQUIRED: Please sign into your Starlink account in the browser window.")
        print("Navigate to the section displaying your data usage chart.")
        print("="*60)
        input("Once the graph is completely visible on your screen, press ENTER here in the terminal to start extraction...")

        # Initialize the explicit wait timer
        wait = WebDriverWait(driver, 15)
        
        # 3. Locate the interactive chart nodes (e.g., SVG rect shapes, or bars)
        print("\nScanning page for chart bars...")
        bars = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, "//*[local-name()='rect' or contains(@class, 'bar') or contains(@class, 'point')]")
        ))
        
        extracted_data = []
        actions = ActionChains(driver)
        
        print(f"Found {len(bars)} interactive elements. Starting hover routine...")
        
        for index, bar in enumerate(bars):
            try:
                # Scroll the target bar smoothly to the center of the viewport
                driver.execute_script("arguments.scrollIntoView({block: 'center'});", bar)
                time.sleep(0.1) 
                
                # Command the mouse driver to float over the specific bar element
                actions.move_to_element(bar).perform()
                time.sleep(0.2)  # Short wait to allow the tooltip pop-up styling engine to build the layout
                
                # Find the dynamic pop-up tooltip block
                tooltip = driver.find_element(By.XPATH, "//*[contains(@class, 'tooltip') or contains(@id, 'tooltip')]")
                tooltip_text = tooltip.text.strip()
                
                if tooltip_text:
                    # Strip out newline breaks to cleanly map data inside a singular string cell
                    cleaned_text = " ".join(tooltip_text.splitlines())
                    print(f"[{index + 1}] Successfully Scraped: {cleaned_text}")
                    extracted_data.append([cleaned_text])
                    
            except Exception:
                # Silently catch elements that aren't functional data bars to prevent breaking the loop
                continue
                
        # 4. Export the structural array to CSV
        if extracted_data:
            with open(output_csv_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Live Chart Hover Text"])
                writer.writerows(extracted_data)
            print(f"\nExtraction complete! Data successfully written to: {output_csv_path}")
        else:
            print("\nNo tooltip text extracted. Check if the chart layout uses custom non-standard markup classes.")
            
    finally:
        # Safely disconnect the session and shut down the browser engine
        driver.quit()

# Execute run targeting Firefox
extract_graph_via_hover_firefox("starlink_firefox_usage.csv")