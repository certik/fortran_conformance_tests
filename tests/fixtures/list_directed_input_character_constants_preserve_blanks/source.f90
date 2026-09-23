! rule: S13.10.2-001
! covers: character-constants-preserve-blanks
! Oracle values are hand-derived from Fortran 2023 13.10.2, 13.10.3.1, or 13.10.3.2.
program list_directed_input_character_constants_preserve_blanks
  implicit none
  integer :: checks, stray
  character(len=6) :: rec
  character(len=4) :: text
  checks=0
  stray=-909
  text='ZZZZ'
  rec = "'A  B'"
  read(rec,*) text
  if (len(text) /= 4) then
    write(*,'(a)') 'LDI:character_constants_preserve_blanks:preserved-blanks-len'
    error stop
  end if
  checks=checks+1
  if (text /= 'A  B') then
    write(*,'(a)') 'LDI:character_constants_preserve_blanks:preserved-blanks'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'LDI:character_constants_preserve_blanks:check-total'
    error stop
  end if
  write(*,'(a)') 'LIST DIRECTED INPUT CHARACTER CONSTANTS PRESERVE BLANKS OK'
end program list_directed_input_character_constants_preserve_blanks
