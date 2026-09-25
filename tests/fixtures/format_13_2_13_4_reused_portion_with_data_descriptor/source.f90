! rule: S13.4-010
! covers: reused-portion-with-data-descriptor
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_reused_portion_with_data_descriptor
  implicit none
  integer :: checks
  character(len=2) :: rec(2)
  character(len=4) :: observed
  checks = 0
  rec = '#'
  observed = '####'
  write(rec,'(SS,"X",(I1))') 1,2
  observed = rec(1) // rec(2)
  if (len(observed) /= 4) then
    write(*,'(a)') 'F132134:reused_portion_with_data_descriptor:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (observed /= 'X12 ') then
    write(*,'(a)') 'F132134:reused_portion_with_data_descriptor:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:reused_portion_with_data_descriptor:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 REUSED_PORTION_WITH_DATA_DESCRIPTOR OK'
end program f132134_reused_portion_with_data_descriptor
