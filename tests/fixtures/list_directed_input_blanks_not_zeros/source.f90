! rule: S13.10.3.1-001
! covers: blanks-not-zeros
! Oracle values are hand-derived from Fortran 2023 13.10.2, 13.10.3.1, or 13.10.3.2.
program list_directed_input_blanks_not_zeros
  implicit none
  integer :: checks, stray
  character(len=3) :: rec
  integer :: a, b
  checks=0
  stray=-909
  a=-501
  b=-502
  rec = "1 2"
  read(rec,*) a, b
  if (a /= 1) then
    write(*,'(a)') 'LDI:blanks_not_zeros:first'
    error stop
  end if
  checks=checks+1
  if (b /= 2) then
    write(*,'(a)') 'LDI:blanks_not_zeros:second'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'LDI:blanks_not_zeros:check-total'
    error stop
  end if
  write(*,'(a)') 'LIST DIRECTED INPUT BLANKS NOT ZEROS OK'
end program list_directed_input_blanks_not_zeros
