! rule: S13.4-004
! covers: repeated-data-descriptor
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_repeated_data_descriptor
  implicit none
  integer :: checks
  character(len=6) :: buf
  checks = 0
  buf = '######'
  write(buf,'(SS,3I2)') 1,2,3
  if (len(buf) /= 6) then
    write(*,'(a)') 'F132134:repeated_data_descriptor:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= ' 1 2 3') then
    write(*,'(a)') 'F132134:repeated_data_descriptor:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:repeated_data_descriptor:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 REPEATED_DATA_DESCRIPTOR OK'
end program f132134_repeated_data_descriptor
