! rule: S13.4-009
! covers: complete-format-terminates-without-item
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_complete_format_terminates_without_item
  implicit none
  integer :: checks
  character(len=2) :: buf
  checks = 0
  buf = '##'
  write(buf,'(SS,I1)') 7
  if (len(buf) /= 2) then
    write(*,'(a)') 'F132134:complete_format_terminates_without_item:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '7 ') then
    write(*,'(a)') 'F132134:complete_format_terminates_without_item:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:complete_format_terminates_without_item:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 COMPLETE_FORMAT_TERMINATES_WITHOUT_ITEM OK'
end program f132134_complete_format_terminates_without_item
