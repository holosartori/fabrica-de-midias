                diff_anual = novo['valor_real_anual'] - atual['valor_real_anual']
                diff_pct = (diff_anual / atual['valor_real_anual'] * 100) if atual['valor_real_anual'] else 0
                sinal_label = "🟢 ganho" if diff_anual > 0 else ("🔴 perda" if diff_anual < 0 else "⚪ igual")
                st.metric("Diferença anual", f"R$ {diff_anual:+,.2f}", delta=f"{diff_pct:+.1f}%")
                st.caption(sinal_label)
            st.markdown("---")
            st.markdown("### 🎯 Veredicto Final")
            if diff_anual > 5000:
                st.success(
                    f"✅ **Vale muito a pena mudar!** Ganho anual de **R$ {diff_anual:,.2f}** "
                    f"({diff_pct:+.1f}%). Diferença significativa em todos os cenários."
                )
            elif diff_anual > 1500:
                st.success(
                    f"✅ **Vale considerar.** Diferença anual de **R$ {diff_anual:,.2f}** "
                    f"({diff_pct:+.1f}%). Pense em outros fatores (crescimento, cultura, distância)."
                )
            elif diff_anual > -1500:
                pct_nominal = ((salario_novo - salario_atual) / salario_atual * 100) if salario_atual else 0
                st.info(
                    f"⚖️ **Diferença quase nula no valor real** (R$ {diff_anual:+,.2f}/ano, {diff_pct:+.1f}%).\n\n"
                    f"📊 Mas o **salário nominal** parece ter subido **{pct_nominal:+.0f}%**! "
                    "Acontece porque os benefícios perdidos compensam (ou superam) o aumento.\n\n"
                    "👉 **A decisão deve ser por outros fatores**: cargo, crescimento, qualidade de vida, "
                    "estabilidade, cultura da empresa. O dinheiro é parecido."
                )
            elif diff_anual > -5000:
                st.warning(
                    f"⚠️ **Cuidado! A nova oferta é R$ {abs(diff_anual):,.2f}/ano MENOR** "
                    f"({diff_pct:+.1f}%). Só vale se houver outros ganhos claros."
                )
            else:
                st.error(
                    f"🛑 **Não compensa financeiramente!** Você perderia R$ {abs(diff_anual):,.2f}/ano. "
                    "Só aceite por motivos não-financeiros muito fortes."
                )
            # Exemplo de como poderia estar o cálculo, didático
            with st.expander("💡 Por que a diferença real é menor que o salário sugere?"):
                st.markdown(
                    f"**Salário atual:** R$ {salario_atual:,.2f} → **Salário novo:** R$ {salario_novo:,.2f}\n\n"
                    f"📈 Aumento **nominal**: **+{((salario_novo - salario_atual) / salario_atual * 100) if salario_atual else 0:.0f}%** no papel\n\n"
                    f"💰 Aumento **real** (considerando benefícios perdidos/ganhos): **{diff_pct:+.1f}%** no ano\n\n"
                    "Quando você perde VR+VA+Prev.Privada+PLR, por exemplo, esses são valores que "
                    "você **recebia todo mês** ou todo ano sem desconto. Trocar por um salário maior "
                    "mas sem esses benefícios pode **não compensar** financeiramente — e o pior, "
                    "você só vai descobrir depois que aceitar.\n\n"
                    "**Por isso essa calculadora existe:** pra você ver o valor real ANTES de decidir. 😉"
