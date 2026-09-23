! rule: S13.10.2-002
! covers: repeat-null
! Oracle values are hand-derived from Fortran 2023 13.10.2, 13.10.3.1, or 13.10.3.2.
program list_directed_input_repeat_null
  implicit none
  integer :: checks, stray
  character(len=3) :: rec
  integer :: x(3)
  checks=0
  stray=-909
  x=[101,202,303]
  rec = "2*"
  read(rec,*) x(1), x(2)
  if (x(1) /= 101) then
    write(*,'(a)') 'LDI:repeat_null:sentinel-1'
    error stop
  end if
  checks=checks+1
  if (x(2) /= 202) then
    write(*,'(a)') 'LDI:repeat_null:sentinel-2'
    error stop
  end if
  checks=checks+1
  if (x(3) /= 303) then
    write(*,'(a)') 'LDI:repeat_null:sentinel-3'
    error stop
  end if
  checks=checks+1
  if (checks /= 3) then
    write(*,'(a)') 'LDI:repeat_null:check-total'
    error stop
  end if
  write(*,'(a)') 'LIST DIRECTED INPUT REPEAT NULL OK'
end program list_directed_input_repeat_null
