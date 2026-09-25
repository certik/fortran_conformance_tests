! rule: S13.4-006
! covers: data-descriptor-transfers-and-proceeds
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_data_descriptor_transfers_and_proceeds
  implicit none
  integer :: checks
  character(len=2) :: buf
  checks = 0
  buf = '##'
  write(buf,'(SS,I1,I1)') 6,8
  if (len(buf) /= 2) then
    write(*,'(a)') 'F132134:data_descriptor_transfers_and_proceeds:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '68') then
    write(*,'(a)') 'F132134:data_descriptor_transfers_and_proceeds:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:data_descriptor_transfers_and_proceeds:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 DATA_DESCRIPTOR_TRANSFERS_AND_PROCEEDS OK'
end program f132134_data_descriptor_transfers_and_proceeds
