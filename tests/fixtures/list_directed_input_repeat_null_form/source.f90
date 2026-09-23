! rule: S13.10.3.2-001
! covers: repeat-null-form
! Oracle values are hand-derived from Fortran 2023 13.10.2, 13.10.3.1, or 13.10.3.2.
program list_directed_input_repeat_null_form
  implicit none
  integer :: checks, stray
  character(len=3) :: rec
  integer :: x
  checks=0
  stray=-909
  x=907
  rec = "1*"
  read(rec,*) x
  if (x /= 907) then
    write(*,'(a)') 'LDI:repeat_null_form:sentinel-preserved'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'LDI:repeat_null_form:check-total'
    error stop
  end if
  write(*,'(a)') 'LIST DIRECTED INPUT REPEAT NULL FORM OK'
end program list_directed_input_repeat_null_form
