    def get_processed_recipes(self) -> List[Recipe]:
        results = []
        for r in self.recipes:
            total_input_cost = 0
            total_output_val = 0
            
            input_details = []
            output_details = []

            # Calculate Inputs
            for iid in r['inputs']:
                sid = str(iid)
                price = 0
                if sid in self.prices:
                    p = self.prices[sid]
                    # Cost = Low (Patient) or High (Instant). Let's stick to Low for profit potential.
                    price = p.get('low', 0)
                    if not price: price = p.get('high', 0)

                total_input_cost += price
                input_details.append({
                    "id": iid, 
                    "name": self.id_to_name.get(iid, f"Item {iid}")
                })

            # Calculate Outputs
            for iid in r['outputs']:
                sid = str(iid)
                price = 0
                if sid in self.prices:
                    p = self.prices[sid]
                    # Revenue = High (Patient) or Low (Instant). Stick to High.
                    price = p.get('high', 0)
                    if not price: price = p.get('low', 0)
                    
                    # Apply Tax
                    revenue = price - self.calculate_tax(price)
                    total_output_val += revenue
                
                output_details.append({
                    "id": iid, 
                    "name": self.id_to_name.get(iid, f"Item {iid}")
                })

            profit = total_output_val - total_input_cost
            roi = (profit / total_input_cost * 100) if total_input_cost > 0 else 0
            
            results.append(Recipe(
                id=r['id'],
                name=r['name'],
                inputs=input_details,
                outputs=output_details,
                profit_margin=int(profit),
                roi=round(roi, 2),
                is_profitable=profit > 0
            ))
            
        return results
