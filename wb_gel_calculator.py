import tkinter as tk
from tkinter import ttk, messagebox
from itertools import product
import math

class WBGelCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("WB胶浓度稀释计算器")
        self.root.geometry("900x700")
        
        # 市售胶浓度（显示值，实际浓度是2倍）
        self.standard_concentrations = [4.5,5.0, 6.0, 7.5, 8.0, 10.0, 12.5, 15.0]
        
        self.setup_ui()
    
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 胶浓度选择
        gel_frame = ttk.LabelFrame(main_frame, text="选择胶浓度 (所有选中的胶都必须使用，实际浓度为显示值的2倍)", padding="5")
        gel_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.gel_vars = {}
        for i, conc in enumerate(self.standard_concentrations):
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(gel_frame, text=f"{conc}%", variable=var)
            chk.grid(row=i//4, column=i%4, sticky=tk.W, padx=5, pady=2)
            self.gel_vars[conc] = var
        
        # 目标参数
        param_frame = ttk.LabelFrame(main_frame, text="目标参数", padding="5")
        param_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 目标总体积
        ttk.Label(param_frame, text="目标总体积 (ml):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.total_volume_var = tk.StringVar(value="10.0")
        ttk.Entry(param_frame, textvariable=self.total_volume_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # 目标胶浓度
        ttk.Label(param_frame, text="目标胶浓度 (%):").grid(row=0, column=2, sticky=tk.W, pady=2, padx=(20,0))
        self.target_conc_var = tk.StringVar(value="8.0")
        ttk.Entry(param_frame, textvariable=self.target_conc_var, width=10).grid(row=0, column=3, sticky=tk.W, pady=2)
        
        # 计算按钮
        ttk.Button(main_frame, text="计算", command=self.calculate).grid(row=2, column=0, columnspan=2, pady=10)
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text="计算结果 (显示前10组最优解，整数解优先)", padding="5")
        result_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 创建树状视图显示结果
        columns = ("序号", "胶用量", "缓冲液用量", "缓冲液比例", "实际浓度", "解类型")
        self.tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=12)
        
        # 设置列宽
        column_widths = [50, 300, 100, 100, 100, 100]
        for col, width in zip(columns, column_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=tk.CENTER)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
    
    def calculate(self):
        try:
            # 获取输入值
            total_volume = float(self.total_volume_var.get())
            target_concentration = float(self.target_conc_var.get())
            
            # 获取选中的胶浓度
            selected_gels = [conc for conc, var in self.gel_vars.items() if var.get()]
            
            if not selected_gels:
                messagebox.showerror("错误", "请至少选择一种胶浓度")
                return
            
            # 验证输入
            if total_volume <= 0:
                raise ValueError("目标总体积必须大于0")
            if target_concentration <= 0:
                raise ValueError("目标胶浓度必须大于0")
            
            # 计算所有解
            solutions = self.find_solutions(selected_gels, target_concentration, total_volume)
            
            # 显示结果
            self.display_results(solutions, selected_gels, total_volume, target_concentration)
            
        except ValueError as e:
            messagebox.showerror("输入错误", str(e))
        except Exception as e:
            messagebox.showerror("计算错误", f"计算过程中发生错误: {str(e)}")
    
    def find_solutions(self, selected_gels, target_conc, total_volume):
        """
        使用数学方法求解所有可能的配比
        注意：胶浓度是稀释后的值，实际浓度是2倍
        """
        solutions = []
        n_gels = len(selected_gels)
        
        # 计算目标总胶质量（注意：胶浓度需要乘以2得到实际浓度）
        target_gel_mass = target_conc * total_volume
        
        # 实际胶浓度（2倍显示值）
        actual_gel_concentrations = [conc * 2 for conc in selected_gels]
        
        if n_gels == 1:
            # 单一胶浓度 - 精确解
            c_actual = actual_gel_concentrations[0]
            v_gel = target_gel_mass / c_actual
            buffer_vol = total_volume - v_gel
            
            if v_gel > 0 and buffer_vol >= 0:
                solutions.append({
                    'volumes': [v_gel],
                    'buffer_volume': buffer_vol,
                    'actual_conc': target_conc,
                    'score': self.calculate_score([v_gel], buffer_vol, total_volume)
                })
        
        elif n_gels == 2:
            # 两个胶浓度 - 线性方程
            c1_actual, c2_actual = actual_gel_concentrations
            # 方程: c1_actual*v1 + c2_actual*v2 = target_gel_mass
            # v1 + v2 <= total_volume
            
            # 生成各种可能的v1值（步长0.1ml）
            max_steps = int(total_volume * 10) + 1
            for v1 in range(1, max_steps):
                v1_ml = v1 / 10.0
                v2_ml = (target_gel_mass - c1_actual * v1_ml) / c2_actual
                
                if v2_ml > 0 and (v1_ml + v2_ml) <= total_volume:
                    buffer_vol = total_volume - (v1_ml + v2_ml)
                    actual_concentration = (c1_actual * v1_ml + c2_actual * v2_ml) / total_volume
                    
                    if abs(actual_concentration - target_conc) < 0.001:
                        solutions.append({
                            'volumes': [v1_ml, v2_ml],
                            'buffer_volume': buffer_vol,
                            'actual_conc': actual_concentration,
                            'score': self.calculate_score([v1_ml, v2_ml], buffer_vol, total_volume)
                        })
        
        else:
            # 三个或更多胶浓度 - 使用优化方法
            solutions = self.solve_multiple_gels(selected_gels, actual_gel_concentrations, target_conc, total_volume)
        
        # 添加最大使用量解
        max_usage_solutions = self.find_max_usage_solutions(selected_gels, actual_gel_concentrations, target_conc, total_volume)
        solutions.extend(max_usage_solutions)
        
        # 去重并排序
        unique_solutions = self.remove_duplicate_solutions(solutions)
        unique_solutions.sort(key=lambda x: x['score'], reverse=True)
        
        return unique_solutions[:10]
    
    def solve_multiple_gels(self, selected_gels, actual_concentrations, target_conc, total_volume):
        """
        解决多个胶浓度的情况
        """
        solutions = []
        n_gels = len(selected_gels)
        target_gel_mass = target_conc * total_volume
        
        # 使用固定步长搜索
        step = 0.5  # 0.5ml步长
        max_steps = int(total_volume / step) + 1
        
        # 为前n-1个胶生成体积组合
        for volumes in product([i * step for i in range(1, max_steps)], repeat=n_gels-1):
            # 确保所有选中的胶都被使用（体积>0）
            if any(v <= 0 for v in volumes):
                continue
            
            total_used_volume = sum(volumes)
            if total_used_volume >= total_volume:
                continue
            
            # 计算最后一个胶的体积
            remaining_mass = target_gel_mass - sum(c * v for c, v in zip(actual_concentrations[:-1], volumes))
            last_volume = remaining_mass / actual_concentrations[-1]
            
            if last_volume > 0 and (total_used_volume + last_volume) <= total_volume:
                all_volumes = list(volumes) + [last_volume]
                buffer_vol = total_volume - sum(all_volumes)
                
                # 验证浓度
                actual_concentration = sum(c * v for c, v in zip(actual_concentrations, all_volumes)) / total_volume
                if abs(actual_concentration - target_conc) < 0.001:  # 允许微小误差
                    solutions.append({
                        'volumes': all_volumes,
                        'buffer_volume': buffer_vol,
                        'actual_conc': actual_concentration,
                        'score': self.calculate_score(all_volumes, buffer_vol, total_volume)
                    })
        
        return solutions
    
    def find_max_usage_solutions(self, selected_gels, actual_concentrations, target_conc, total_volume):
        """
        找到各种最大使用量的解
        """
        solutions = []
        n_gels = len(selected_gels)
        target_gel_mass = target_conc * total_volume
        
        # 为每种胶生成一个最大使用量解
        for i in range(n_gels):
            # 让第i种胶使用最大可能量，其他胶按比例分配剩余质量
            max_volumes = [0.1] * n_gels  # 所有胶至少用0.1ml
            
            # 第i种胶用较大体积
            max_volumes[i] = total_volume * 0.6  # 用60%的总体积
            
            # 调整其他胶的体积以满足浓度要求
            current_mass = sum(c * v for c, v in zip(actual_concentrations, max_volumes))
            
            if current_mass > 0:
                scale_factor = target_gel_mass / current_mass
                
                # 按比例缩放所有体积
                scaled_volumes = [v * scale_factor for v in max_volumes]
                total_gel_vol = sum(scaled_volumes)
                
                if total_gel_vol <= total_volume:
                    buffer_vol = total_volume - total_gel_vol
                    actual_concentration = sum(c * v for c, v in zip(actual_concentrations, scaled_volumes)) / total_volume
                    
                    if abs(actual_concentration - target_conc) < 0.001:
                        solutions.append({
                            'volumes': scaled_volumes,
                            'buffer_volume': buffer_vol,
                            'actual_conc': actual_concentration,
                            'score': self.calculate_score(scaled_volumes, buffer_vol, total_volume) - i  # 稍微调整分数以区分不同解
                        })
        
        # 添加均衡使用解
        balanced_volumes = [total_volume * 0.8 / n_gels] * n_gels  # 每种胶用相似体积
        current_mass = sum(c * v for c, v in zip(actual_concentrations, balanced_volumes))
        
        if current_mass > 0:
            scale_factor = target_gel_mass / current_mass
            scaled_volumes = [v * scale_factor for v in balanced_volumes]
            total_gel_vol = sum(scaled_volumes)
            
            if total_gel_vol <= total_volume:
                buffer_vol = total_volume - total_gel_vol
                actual_concentration = sum(c * v for c, v in zip(actual_concentrations, scaled_volumes)) / total_volume
                
                if abs(actual_concentration - target_conc) < 0.001:
                    solutions.append({
                        'volumes': scaled_volumes,
                        'buffer_volume': buffer_vol,
                        'actual_conc': actual_concentration,
                        'score': self.calculate_score(scaled_volumes, buffer_vol, total_volume) + 10  # 均衡解额外加分
                    })
        
        return solutions
    
    def calculate_score(self, volumes, buffer_volume, total_volume):
        """
        计算解的评分，整数解优先
        """
        score = 0
        
        # 整数解加分（主要评分标准）
        if all(abs(v - round(v)) < 0.001 for v in volumes) and abs(buffer_volume - round(buffer_volume)) < 0.001:
            score += 1000  # 整数解大幅加分
        
        # 体积数值简单加分（能被0.5, 1, 2, 5整除）
        for v in volumes:
            if v > 0:
                if v == round(v):  # 整数
                    score += 100
                elif v * 2 == round(v * 2):  # 0.5的倍数
                    score += 50
                elif v * 10 == round(v * 10):  # 0.1的倍数
                    score += 20
        
        if buffer_volume == round(buffer_volume):  # 整数缓冲液
            score += 50
        
        # 使用多种胶加分（多样性）
        used_gels = sum(1 for v in volumes if v > 0.1)  # 大于0.1ml算使用
        score += used_gels * 10
        
        # 缓冲液比例适中加分（10%-90%）
        buffer_ratio = buffer_volume / total_volume
        if 0.1 <= buffer_ratio <= 0.9:
            score += 30
        
        # 避免极端体积加分
        if all(0.1 <= v <= total_volume * 0.8 for v in volumes):
            score += 20
        
        return score
    
    def remove_duplicate_solutions(self, solutions):
        """
        去除重复的解
        """
        unique_solutions = []
        seen = set()
        
        for sol in solutions:
            # 创建解的指纹（四舍五入到小数点后2位）
            fingerprint = tuple(round(v, 2) for v in sol['volumes'])
            
            if fingerprint not in seen:
                seen.add(fingerprint)
                unique_solutions.append(sol)
        
        return unique_solutions
    
    def display_results(self, solutions, selected_gels, total_volume, target_conc):
        # 清空现有结果
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not solutions:
            self.tree.insert("", "end", values=("无解", "无法找到满足条件的配比", "", "", "", ""))
            return
        
        for i, sol in enumerate(solutions, 1):
            # 构建胶用量字符串
            gel_usage = []
            for j, vol in enumerate(sol['volumes']):
                gel_usage.append(f"{selected_gels[j]}%胶: {vol:.2f}ml")
            gel_usage_str = " + ".join(gel_usage)
            
            # 确定解类型
            if all(abs(v - round(v)) < 0.001 for v in sol['volumes']):
                solution_type = "整数解"
            else:
                solution_type = "小数解"
            
            buffer_ratio = sol['buffer_volume'] / total_volume * 100
            
            self.tree.insert("", "end", values=(
                i,
                gel_usage_str,
                f"{sol['buffer_volume']:.2f}ml",
                f"{buffer_ratio:.1f}%",
                f"{sol['actual_conc']:.4f}%",
                solution_type
            ))

def main():
    root = tk.Tk()
    app = WBGelCalculator(root)
    root.mainloop()

if __name__ == "__main__":
    main()