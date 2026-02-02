import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_web_visualization():
    print("Starting Cooperative Kitchen Simulation...")
    print("Opening browser at http://127.0.0.1:8521")
    print("Press Ctrl+C to stop the server.\n")
    
    from visualization.server import create_server
    
    server = create_server()
    server.port = 8521
    server.launch()


def run_console_mode(max_steps: int = 500):
    print("Running simulation in console mode...")
    print(f"Max steps: {max_steps}\n")
    
    from model.kitchen_model import KitchenModel
    
    model = KitchenModel(num_cooks=4)
    
    for i in range(max_steps):
        model.step()
        if model.game_over:
            break
    
    print("\n" + "=" * 60)
    print("SIMULATION COMPLETE")
    print("=" * 60)
    print(f"Total time steps: {model.time_steps}")
    print(f"Completed orders: {model.order_manager.get_completed_count()}")
    print(f"Failed orders: {model.order_manager.get_failed_count()}")
    print(f"Result: {'WIN' if model.game_result == 'win' else 'LOSE' if model.game_result == 'lose' else 'INCOMPLETE'}")


def run_test():
    print("Running quick test simulation (50 steps)...\n")
    
    from model.kitchen_model import KitchenModel
    
    model = KitchenModel(num_cooks=4)
    
    for i in range(50):
        model.step()
        if model.game_over:
            break
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print(f"Time steps completed: {model.time_steps}")
    print(f"Orders completed: {model.order_manager.get_completed_count()}")
    print(f"Orders failed: {model.order_manager.get_failed_count()}")
    print(f"Active orders: {model.order_manager.get_active_count()}")
    
    issues = []
    
    if model.order_manager.get_completed_count() == 0 and model.time_steps > 30:
        issues.append("No orders completed after 30+ steps")
    
    if len(model.cooks) != 4:
        issues.append(f"Expected 4 cooks, found {len(model.cooks)}")
    
    if model.head_chef is None:
        issues.append("Head Chef not initialized")
    
    if issues:
        print("\nISSUES DETECTED:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\nAll basic checks passed!")
    
    return len(issues) == 0


def run_matplotlib_visualization():
    print("Starting Cooperative Kitchen Simulation (Matplotlib mode)...")
    print("Close the window to stop.\n")
    
    from run_simple import run_simulation
    run_simulation()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg == "--console":
            steps = int(sys.argv[2]) if len(sys.argv) > 2 else 500
            run_console_mode(steps)
        elif arg == "--test":
            success = run_test()
            sys.exit(0 if success else 1)
        elif arg == "--web":
            run_web_visualization()
        elif arg == "--help":
            print(__doc__)
        else:
            print(f"Unknown argument: {arg}")
            print("Use --help for usage information.")
    else:
        run_matplotlib_visualization()
