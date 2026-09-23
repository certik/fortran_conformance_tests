! rule: S13.10.2-001
! covers: multiple-blanks-collapse
! Oracle values are hand-derived from Fortran 2023 13.10.2, 13.10.3.1, or 13.10.3.2.
program list_directed_input_multiple_blanks_collapse
  implicit none
  integer :: checks, stray
  character(len=5) :: rec
  integer :: a, b
  checks=0
  stray=-909
  a=-111
  b=-222
  rec = "1   2"
  read(rec,*) a, b
  if (a /= 1) then
    write(*,'(a)') 'LDI:multiple_blanks_collapse:first-value'
    error stop
  end if
  checks=checks+1
  if (b /= 2) then
    write(*,'(a)') 'LDI:multiple_blanks_collapse:second-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'LDI:multiple_blanks_collapse:check-total'
    error stop
  end if
  write(*,'(a)') 'LIST DIRECTED INPUT MULTIPLE BLANKS COLLAPSE OK'
end program list_directed_input_multiple_blanks_collapse
