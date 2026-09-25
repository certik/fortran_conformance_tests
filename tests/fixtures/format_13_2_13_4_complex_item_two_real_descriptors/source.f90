! rule: S13.4-005
! covers: complex-item-two-real-descriptors
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_complex_item_two_real_descriptors
  implicit none
  integer :: checks
  character(len=10) :: buf
  complex :: z
  checks = 0
  buf = '##########'
  z = cmplx(2.5, -3.5)
  write(buf,'(SS,F5.1,F5.1)') z
  if (len(buf) /= 10) then
    write(*,'(a)') 'F132134:complex_item_two_real_descriptors:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '  2.5 -3.5') then
    write(*,'(a)') 'F132134:complex_item_two_real_descriptors:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:complex_item_two_real_descriptors:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 COMPLEX_ITEM_TWO_REAL_DESCRIPTORS OK'
end program f132134_complex_item_two_real_descriptors
