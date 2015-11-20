*$ CREATE MGDRAW.FOR
*COPY MGDRAW
*                                                                      *
*=== mgdraw ===========================================================*
*                                                                      *
      SUBROUTINE MGDRAW ( ICODE, MREG )

      INCLUDE '(DBLPRC)'
      INCLUDE '(DIMPAR)'
      INCLUDE '(IOUNIT)'
*
*----------------------------------------------------------------------*
*                                                                      *
*     Copyright (C) 1990-2006      by        Alfredo Ferrari           *
*     All Rights Reserved.                                             *
*                                                                      *
*                                                                      *
*     MaGnetic field trajectory DRAWing: actually this entry manages   *
*                                        all trajectory dumping for    *
*                                        drawing                       *
*                                                                      *
*     Created on   01 march 1990   by        Alfredo Ferrari           *
*                                              INFN - Milan            *
*     Last change  05-may-06       by        Alfredo Ferrari           *
*                                              INFN - Milan            *
*                                                                      *
*----------------------------------------------------------------------*
*
      INCLUDE '(CASLIM)'
      INCLUDE '(COMPUT)'
      INCLUDE '(SOURCM)'
      INCLUDE '(FHEAVY)'
      INCLUDE '(FLKSTK)'
      INCLUDE '(GENSTK)'
      INCLUDE '(MGDDCM)'
      INCLUDE '(PAPROP)'
      INCLUDE '(QUEMGD)'
      INCLUDE '(SUMCOU)'
      INCLUDE '(TRACKR)'
*
      DIMENSION DTQUEN ( MXTRCK, MAXQMG )
*
      CHARACTER*20 FILNAM
      LOGICAL LFCOPE
      SAVE LFCOPE
      DATA LFCOPE / .FALSE. /
*
*----------------------------------------------------------------------*
*                                                                      *
*     Icode = 1: call from Kaskad                                      *
*     Icode = 2: call from Emfsco                                      *
*     Icode = 3: call from Kasneu                                      *
*     Icode = 4: call from Kashea                                      *
*     Icode = 5: call from Kasoph                                      *
*                                                                      *
*----------------------------------------------------------------------*
*                                                                      *
      IF ( .NOT. LFCOPE ) THEN
         LFCOPE = .TRUE.
         IF ( KOMPUT .EQ. 2 ) THEN
            FILNAM = '/'//CFDRAW(1:8)//' DUMP A'
         ELSE
            FILNAM = CFDRAW
         END IF
         OPEN ( UNIT = IODRAW, FILE = FILNAM, STATUS = 'NEW', FORM =
     &          'UNFORMATTED' )
      END IF
      WRITE (IODRAW) NTRACK, MTRACK, JTRACK, SNGL (ETRACK),
     &               SNGL (WTRACK)
      WRITE (IODRAW) ( SNGL (XTRACK (I)), SNGL (YTRACK (I)),
     &                 SNGL (ZTRACK (I)), I = 0, NTRACK ),
     &               ( SNGL (DTRACK (I)), I = 1, MTRACK ),
     &                 SNGL (CTRACK)
Cx,y,ztrck
      if (etrack.ge.10) write(89,'(6E19.10,I3,I3,E19.10)')CXTRCK,CYTRCK, 
     &     CZTRCK, XTRACK(0),YTRACK(0),ZTRACK(0),JTRACK,NCASE,ATRACK
* -- rk      if (etrack.ge.10) write(90,'(7E16.7,I3)') TXFLK(I), TYFLK(I), 
* -- rk    &     TZFLK(I),XTRACK(I),YTRACK(I),ZTRACK(I),ETRACK,JTRACK
*  +-------------------------------------------------------------------*
*  |  Quenching is activated
      IF ( LQEMGD ) THEN
         IF ( MTRACK .GT. 0 ) THEN
            RULLL  = ZERZER
            CALL QUENMG ( ICODE, MREG, RULLL, DTQUEN )
            WRITE (IODRAW) ( ( SNGL (DTQUEN (I,JBK)), I = 1, MTRACK ),
     &                         JBK = 1, NQEMGD )
         END IF
      END IF
*  |  End of quenching
*  +-------------------------------------------------------------------*
      RETURN
*
*======================================================================*
*                                                                      *
*     Boundary-(X)crossing DRAWing:                                    *
*                                                                      *
*     Icode = 1x: call from Kaskad                                     *
*             19: boundary crossing                                    *
*     Icode = 2x: call from Emfsco                                     *
*             29: boundary crossing                                    *
*     Icode = 3x: call from Kasneu                                     *
*             39: boundary crossing                                    *
*     Icode = 4x: call from Kashea                                     *
*             49: boundary crossing                                    *
*     Icode = 5x: call from Kasoph                                     *
*             59: boundary crossing                                    *
*                                                                      *
*======================================================================*
*                                                                      *
      ENTRY BXDRAW ( ICODE, MREG, NEWREG, XSCO, YSCO, ZSCO )
      RETURN
*
*======================================================================*
*                                                                      *
*     Event End DRAWing:                                               *
*                                                                      *
*======================================================================*
*                                                                      *
      ENTRY EEDRAW ( ICODE )
      RETURN
*
*======================================================================*
*                                                                      *
*     ENergy deposition DRAWing:                                       *
*                                                                      *
*     Icode = 1x: call from Kaskad                                     *
*             10: elastic interaction recoil                           *
*             11: inelastic interaction recoil                         *
*             12: stopping particle                                    *
*             13: pseudo-neutron deposition                            *
*             14: escape                                               *
*             15: time kill                                            *
*     Icode = 2x: call from Emfsco                                     *
*             20: local energy deposition (i.e. photoelectric)         *
*             21: below threshold, iarg=1                              *
*             22: below threshold, iarg=2                              *
*             23: escape                                               *
*             24: time kill                                            *
*     Icode = 3x: call from Kasneu                                     *
*             30: target recoil                                        *
*             31: below threshold                                      *
*             32: escape                                               *
*             33: time kill                                            *
*     Icode = 4x: call from Kashea                                     *
*             40: escape                                               *
*             41: time kill                                            *
*             42: delta ray stack overflow                             *
*     Icode = 5x: call from Kasoph                                     *
*             50: optical photon absorption                            *
*             51: escape                                               *
*             52: time kill                                            *
*                                                                      *
*======================================================================*
*                                                                      *
      ENTRY ENDRAW ( ICODE, MREG, RULL, XSCO, YSCO, ZSCO )
      IF ( .NOT. LFCOPE ) THEN
         LFCOPE = .TRUE.
         IF ( KOMPUT .EQ. 2 ) THEN
            FILNAM = '/'//CFDRAW(1:8)//' DUMP A'
         ELSE
            FILNAM = CFDRAW
         END IF
         OPEN ( UNIT = IODRAW, FILE = FILNAM, STATUS = 'NEW', FORM =
     &          'UNFORMATTED' )
      END IF
      WRITE (IODRAW)  0, ICODE, JTRACK, SNGL (ETRACK), SNGL (WTRACK)
      WRITE (IODRAW)  SNGL (XSCO), SNGL (YSCO), SNGL (ZSCO), SNGL (RULL)
*  +-------------------------------------------------------------------*
*  |  Quenching is activated : calculate quenching factor
*  |  and store quenched energy in DTQUEN(1, jbk)
      IF ( LQEMGD ) THEN
         RULLL = RULL
         CALL QUENMG ( ICODE, MREG, RULLL, DTQUEN )
         WRITE (IODRAW) ( SNGL (DTQUEN(1, JBK)), JBK = 1, NQEMGD )
      END IF
*  |  end quenching
*  +-------------------------------------------------------------------*
      RETURN
*
*======================================================================*
*                                                                      *
*     SOurce particle DRAWing:                                         *
*                                                                      *
*======================================================================*
*
      ENTRY SODRAW
      IF ( .NOT. LFCOPE ) THEN
         LFCOPE = .TRUE.
         IF ( KOMPUT .EQ. 2 ) THEN
            FILNAM = '/'//CFDRAW(1:8)//' DUMP A'
         ELSE
            FILNAM = CFDRAW
         END IF
         OPEN ( UNIT = IODRAW, FILE = FILNAM, STATUS = 'NEW', FORM =
     &          'UNFORMATTED' )
      END IF
      WRITE (IODRAW) -NCASE, NPFLKA, NSTMAX, SNGL (TKESUM),
     &                SNGL (WEIPRI)
*  +-------------------------------------------------------------------*
*  |  (Radioactive) isotope: it works only for 1 source particle on
*  |  the stack for the time being
      IF ( ILOFLK (NPFLKA) .GE. 100000 .AND. LRADDC (NPFLKA) ) THEN
         IARES  = MOD ( ILOFLK (NPFLKA), 100000  )  / 100
         IZRES  = MOD ( ILOFLK (NPFLKA), 10000000 ) / 100000
         IISRES = ILOFLK (NPFLKA) / 10000000
         IONID  = ILOFLK (NPFLKA)
         WRITE (IODRAW) ( IONID,SNGL(-TKEFLK(I)),
     &                    SNGL (WTFLK(I)), SNGL (XFLK (I)),
     &                    SNGL (YFLK (I)), SNGL (ZFLK (I)),
     &                    SNGL (TXFLK(I)), SNGL (TYFLK(I)),
     &                    SNGL (TZFLK(I)), I = 1, NPFLKA )
*  |
*  +-------------------------------------------------------------------*
*  |  Patch for heavy ions: it works only for 1 source particle on
*  |  the stack for the time being
      ELSE IF ( ABS (ILOFLK (NPFLKA)) .GE. 10000 ) THEN
         IONID = ILOFLK (NPFLKA)
         CALL DCDION ( IONID )
         WRITE (IODRAW) ( IONID,SNGL(TKEFLK(I)+AMNHEA(-IONID)),
     &                    SNGL (WTFLK(I)), SNGL (XFLK (I)),
     &                    SNGL (YFLK (I)), SNGL (ZFLK (I)),
     &                    SNGL (TXFLK(I)), SNGL (TYFLK(I)),
     &                    SNGL (TZFLK(I)), I = 1, NPFLKA )
*  |
*  +-------------------------------------------------------------------*
*  |  Patch for heavy ions: ???
      ELSE IF ( ILOFLK (NPFLKA) .LT. -6 ) THEN
         WRITE (IODRAW) ( IONID,SNGL(TKEFLK(I)+AMNHEA(-ILOFLK(NPFLKA))),
     &                    SNGL (WTFLK(I)), SNGL (XFLK (I)),
     &                    SNGL (YFLK (I)), SNGL (ZFLK (I)),
     &                    SNGL (TXFLK(I)), SNGL (TYFLK(I)),
     &                    SNGL (TZFLK(I)), I = 1, NPFLKA )
*  |
*  +-------------------------------------------------------------------*
*  |
      ELSE
         WRITE (IODRAW) ( ILOFLK(I), SNGL (TKEFLK(I)+AM(ILOFLK(I))),
     &                    SNGL (WTFLK(I)), SNGL (XFLK (I)),
     &                    SNGL (YFLK (I)), SNGL (ZFLK (I)),
     &                    SNGL (TXFLK(I)), SNGL (TYFLK(I)),
     &                    SNGL (TZFLK(I)), I = 1, NPFLKA )
      END IF
*  |
*  +-------------------------------------------------------------------*
      RETURN
*
*======================================================================*
*                                                                      *
*     USer dependent DRAWing:                                          *
*                                                                      *
*     Icode = 10x: call from Kaskad                                    *
*             100: elastic   interaction secondaries                   *
*             101: inelastic interaction secondaries                   *
*             102: particle decay  secondaries                         *
*             103: delta ray  generation secondaries                   *
*             104: pair production secondaries                         *
*             105: bremsstrahlung  secondaries                         *
*             110: decay products                                      *
*     Icode = 20x: call from Emfsco                                    *
*             208: bremsstrahlung secondaries                          *
*             210: Moller secondaries                                  *
*             212: Bhabha secondaries                                  *
*             214: in-flight annihilation secondaries                  *
*             215: annihilation at rest   secondaries                  *
*             217: pair production        secondaries                  *
*             219: Compton scattering     secondaries                  *
*             221: photoelectric          secondaries                  *
*             225: Rayleigh scattering    secondaries                  *
*     Icode = 30x: call from Kasneu                                    *
*             300: interaction secondaries                             *
*     Icode = 40x: call from Kashea                                    *
*             400: delta ray  generation secondaries                   *
*  For all interactions secondaries are put on GENSTK common (kp=1,np) *
*  but for KASHEA delta ray generation where only the secondary elec-  *
*  tron is present and stacked on FLKSTK common for kp=npflka          *
*                                                                      *
*======================================================================*
*
      ENTRY USDRAW ( ICODE, MREG, XSCO, YSCO, ZSCO )
      IF ( .NOT. LFCOPE ) THEN
         LFCOPE = .TRUE.
         IF ( KOMPUT .EQ. 2 ) THEN
            FILNAM = '/'//CFDRAW(1:8)//' DUMP A'
         ELSE
            FILNAM = CFDRAW
         END IF
         OPEN ( UNIT = IODRAW, FILE = FILNAM, STATUS = 'NEW', FORM =
     &          'UNFORMATTED' )
      END IF
* No output by default:
      RETURN
*=== End of subrutine Mgdraw ==========================================*
      END

