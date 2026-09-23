! rule: S13.10.3.1-009
! covers: character-blank-padding
! Oracle values are hand-derived from Fortran 2023 13.10.2, 13.10.3.1, or 13.10.3.2.
program list_directed_input_character_blank_padding
  implicit none
  integer :: checks, stray
  character(len=4) :: rec
  character(len=4) :: text
  checks=0
  stray=-909
  text='ZZZZ'
  rec = "'AB'"
  read(rec,*) text
  if (len(text) /= 4) then
    write(*,'(a)') 'LDI:character_blank_padding:padded-value-len'
    error stop
  end if
  checks=checks+1
  if (text /= 'AB  ') then
    write(*,'(a)') 'LDI:character_blank_padding:padded-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'LDI:character_blank_padding:check-total'
    error stop
  end if
  write(*,'(a)') 'LIST DIRECTED INPUT CHARACTER BLANK PADDING OK'
end program list_directed_input_character_blank_padding
