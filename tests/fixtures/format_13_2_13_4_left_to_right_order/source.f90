! rule: S13.4-003
! covers: left-to-right-order
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_left_to_right_order
  implicit none
  integer :: checks
  character(len=3) :: buf
  checks = 0
  buf = '###'
  write(buf,'(SS,"A",I1,"B")') 7
  if (len(buf) /= 3) then
    write(*,'(a)') 'F132134:left_to_right_order:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= 'A7B') then
    write(*,'(a)') 'F132134:left_to_right_order:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:left_to_right_order:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 LEFT_TO_RIGHT_ORDER OK'
end program f132134_left_to_right_order
