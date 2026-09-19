#include <genesis.h>
#include "collision.h"
#include "globals.h"

bool FUNCAO_CHECK_GUARD(u8 guardFlag, u8 enemy)
{
	bool retorno = FALSE;
	if((guardFlag == 1 || guardFlag == 3) && 
	(
		(P[enemy].state==107 || P[enemy].state==108 || P[enemy].state==109 || P[enemy].state==110) || 
		(P[enemy].state==100 && P[enemy].direcao== 1 && (P[enemy].key_JOY_LEFT_status ==1 || P[enemy].key_JOY_LEFT_status ==2)) || 
		(P[enemy].state==100 && P[enemy].direcao==-1 && (P[enemy].key_JOY_RIGHT_status==1 || P[enemy].key_JOY_RIGHT_status==2)) 
	)){
		retorno = TRUE;
	}
	if((guardFlag == 1 || guardFlag == 2) && 
	(
		(P[enemy].state==207 || P[enemy].state==208 || P[enemy].state==209 || P[enemy].state==210) || 
		(P[enemy].state==200 && P[enemy].direcao== 1 && (P[enemy].key_JOY_LEFT_status ==1 || P[enemy].key_JOY_LEFT_status ==2)) || 
		(P[enemy].state==200 && P[enemy].direcao==-1 && (P[enemy].key_JOY_RIGHT_status==1 || P[enemy].key_JOY_RIGHT_status==2)) 
	)){
		retorno = TRUE;
	}
	return retorno;
}

bool FUNCAO_COLISAO(s16 R1x1, s16 R1y1, s16 R1x2, s16 R1y2, s16 R2x1, s16 R2y1, s16 R2x2, s16 R2y2)
{
	
	s16 temp=0;
	if(R1x1>R1x2){ temp=R1x1; R1x1=R1x2; R1x2=temp; }
	if(R2x1>R2x2){ temp=R2x1; R2x1=R2x2; R2x2=temp; }
	
	if ( (R1x1+(R1x2-R1x1)>R2x1) && (R1x1<R2x1+(R2x2-R2x1)) && 
		 (R1y1+(R1y2-R1y1)>R2y1) && (R1y1<R2y1+(R2y2-R2y1)) )
	{ 
		
		if(R1x1==R1x2 && R1y1==R1y2){
			return 0;
			}else if(R2x1==R2x2 && R2y1==R2y2){
				return 0;
			}else{
				/*houve colisao*/
				return 1;
			}
	}else{ 
		/*nao houve colisao*/
		return 0;
	}
}
