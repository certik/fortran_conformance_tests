! rule: S13.10.2-003
! covers: comma-separator
! Oracle values are hand-derived from Fortran 2023 13.10.2, 13.10.3.1, or 13.10.3.2.
program list_directed_input_comma_separator
  implicit none
  integer :: checks, stray
  character(len=4) :: rec
  integer :: a, b
  checks=0
  stray=-909
  a=-301
  b=-302
  rec = "1, 2"
  read(rec,*) a, b
  if (a /= 1) then
    write(*,'(a)') 'LDI:comma_separator:first'
    error stop
  end if
  checks=checks+1
  if (b /= 2) then
    write(*,'(a)') 'LDI:comma_separator:second'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'LDI:comma_separator:check-total'
    error stop
  end if
  write(*,'(a)') 'LIST DIRECTED INPUT COMMA SEPARATOR OK'
end program list_directed_input_comma_separator
