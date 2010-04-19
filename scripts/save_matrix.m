function [A] = save_matrix(data, filename, ext)
if ( strcmp(ext, 'bdat'))
    [i,j,s] = find(data);
    i = [size(data,1); i];
    j = [size(data,2); j];
    s = [0; s~=0];
    A = [i j s];
    dlmwrite([filename '.' ext], A, 'delimiter', '\t');
elseif ( strcmp(ext, 'ndat'))
    [i,j,s] = find(data);
    i = [size(data,1); i];
    j = [size(data,2); j];
    s = [0; s];
    A = [i j s];
    dlmwrite([filename '.' ext], A, 'delimiter', '\t');
elseif ( strcmp(ext, 'dense') )
     dlmwrite([filename '.' ext], full(data),'precision',1, 'delimiter', ' '); 
     A = data;
elseif ( strcmp(ext, 'cat') | strcmp(ext, 'num') )
     % WARNING ! CAT and NUM files are stored transposed 
     dlmwrite([filename '.' ext], full(data)', 'delimiter', ' '); 
     A = data';
else
    error(['Unknown extension: ' ext ])
end
