
void mx_extractGroup(texcoordGroup_struct data, int index, out float result)
{
    result = data.st_0.ss;

    if (index == 1)
        result = data.st_1.ss;
    else if (index == 2)
        result = data.st_2.ss;
}