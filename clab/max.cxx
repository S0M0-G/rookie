# include <stdio.h>
int main ( ) 
{
    int max,i,tab[10];
    for ( i=0; i<=9;i++)
    { 
        printf ("saisir un entier\n");
        scanf ( "%d",&tab[i] );
    } 
    max=0 ;
    for ( i=0; i<=9 ;i++)
    { 
        if ( tab[i]>max)
        {
            max=tab[i];
        }
    
    } 
    printf("le maximum est %d",max);
    return 0;
}
    