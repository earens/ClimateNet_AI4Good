source ~/.bashrc
conda activate climatenet

echo "variables : \ns1 : $1 \ns2 : $2 \ns3 : $3"
echo "all variables : $@"
model=$1
location=euler

if [[ $location == euler ]]
then
	user="atabin"
    data_folder="/cluster/work/igp_psr/ai4good/group-1b/data/"
    scratch_folder="/cluster/scratch/$user"
    save_dir="$scratch_folder/$model/"
    checkpoint_path="$scratch_folder/checkpoints/$model/"
else
	user="alexis"
    data_folder="/media/alexis/MyPassport/ai4good/"
    save_dir="$data_folder/$model/"
    checkpoint_path="$data_folder/checkpoints/$model/"
fi


echo "Running on $location with following parameters : "
echo "User : $user"
echo "Model : $model"
echo "Data folder : $data_folder"
echo "Saving directory : $save_dir"
echo "Checkpoint path : $checkpoint_path"

python ~/ClimateNet_AI4Good/run.py $model \
    --data_dir $data_folder \
    --checkpoint_path $checkpoint_path \
    --save_dir $save_dir

echo "Done!"
