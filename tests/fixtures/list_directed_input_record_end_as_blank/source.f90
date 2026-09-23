! rule: S13.10.2-001
! covers: record-end-as-blank
! Oracle values are hand-derived from Fortran 2023 13.10.2, 13.10.3.1, or 13.10.3.2.
program list_directed_input_record_end_as_blank
  implicit none
  integer :: checks, stray
  character(len=1) :: recs(2)
  integer :: a, b
  checks=0
  stray=-909
  a=-101
  b=-202
  recs = [character(len=1) :: "1", "2"]
  read(recs,*) a, b
  if (a /= 1) then
    write(*,'(a)') 'LDI:record_end_as_blank:first-value'
    error stop
  end if
  checks=checks+1
  if (b /= 2) then
    write(*,'(a)') 'LDI:record_end_as_blank:second-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'LDI:record_end_as_blank:check-total'
    error stop
  end if
  write(*,'(a)') 'LIST DIRECTED INPUT RECORD END AS BLANK OK'
end program list_directed_input_record_end_as_blank
