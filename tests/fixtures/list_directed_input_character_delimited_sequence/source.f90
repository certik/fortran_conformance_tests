! rule: S13.10.3.1-007
! covers: character-delimited-sequence
! Oracle values are hand-derived from Fortran 2023 13.10.2, 13.10.3.1, or 13.10.3.2.
program list_directed_input_character_delimited_sequence
  implicit none
  integer :: checks, stray
  character(len=7) :: rec
  character(len=5) :: text
  checks=0
  stray=-909
  text='ZZZZZ'
  rec = "'A,B/;'"
  read(rec,*) text
  if (len(text) /= 5) then
    write(*,'(a)') 'LDI:character_delimited_sequence:delimited-value-len'
    error stop
  end if
  checks=checks+1
  if (text /= 'A,B/;') then
    write(*,'(a)') 'LDI:character_delimited_sequence:delimited-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'LDI:character_delimited_sequence:check-total'
    error stop
  end if
  write(*,'(a)') 'LIST DIRECTED INPUT CHARACTER DELIMITED SEQUENCE OK'
end program list_directed_input_character_delimited_sequence
