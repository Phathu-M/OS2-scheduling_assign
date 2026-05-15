# Automates execution of FCFS, SJF, Priority, and MLFQ scheduling algorithms
# across multiple patron counts and seed values.
# Outputs CSV results per run into the results/ directory for analysis.
SCHEDULERS=(0 1 2 3)
PATRON_COUNTS=(10 20 30 50 70 100)
SEEDS=(7 30 42 256 512 999)
SWITCH_TIME=5

mkdir -p results

echo "Compiling..."
javac -d bin src/barScheduling/*.java

if [ $? -ne 0 ]; then
    echo "Compilation failed. Exiting."
    exit 1
fi

echo "Compilation successful."
echo ""

TOTAL=$(( ${#SCHEDULERS[@]} * ${#PATRON_COUNTS[@]} * ${#SEEDS[@]} ))
COUNT=0

for SCHED in "${SCHEDULERS[@]}"; do
    for PATRONS in "${PATRON_COUNTS[@]}"; do
        for SEED in "${SEEDS[@]}"; do

            COUNT=$((COUNT + 1))
            echo "[$COUNT/$TOTAL] Scheduler=$SCHED Patrons=$PATRONS Seed=$SEED"

            echo "---- RUN START ----" >> results/log.txt
            echo "SCHED=$SCHED PATRONS=$PATRONS SEED=$SEED" >> results/log.txt

            java -cp bin barScheduling.SchedulingSimulation \
                $PATRONS $SCHED $SEED $SWITCH_TIME

            echo "---- RUN END ----" >> results/log.txt
            echo "" >> results/log.txt

        done
    done
done

echo ""
echo "All experiments completed."
echo "Check results/ folder and log.txt for run separation."