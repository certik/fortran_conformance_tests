! rule: R1306
! covers: repeat-specification-term
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_repeat_specification_term
  implicit none
  integer :: checks
  character(len=4) :: buf
  checks = 0
  buf = '####'
  write(buf,'(SS,2(I1,"/"))') 4,5
  if (len(buf) /= 4) then
    write(*,'(a)') 'F132134:repeat_specification_term:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '4/5/') then
    write(*,'(a)') 'F132134:repeat_specification_term:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:repeat_specification_term:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 REPEAT_SPECIFICATION_TERM OK'
end program f132134_repeat_specification_term
