! rule: S13.10.3.2-001
! covers: leading-empty-first-record
! Oracle values are hand-derived from Fortran 2023 13.10.2, 13.10.3.1, or 13.10.3.2.
program list_directed_input_leading_empty_first_record
  implicit none
  integer :: checks, stray
  character(len=2) :: rec
  integer :: x, y
  checks=0
  stray=-909
  x=707
  y=808
  rec = ",9"
  read(rec,*) x, y
  if (x /= 707) then
    write(*,'(a)') 'LDI:leading_empty_first_record:x-sentinel'
    error stop
  end if
  checks=checks+1
  if (y /= 9) then
    write(*,'(a)') 'LDI:leading_empty_first_record:y-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'LDI:leading_empty_first_record:check-total'
    error stop
  end if
  write(*,'(a)') 'LIST DIRECTED INPUT LEADING EMPTY FIRST RECORD OK'
end program list_directed_input_leading_empty_first_record
