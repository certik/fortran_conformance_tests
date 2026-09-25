! rule: S13.4-005
! covers: one-data-descriptor-per-item
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_one_data_descriptor_per_item
  implicit none
  integer :: checks
  character(len=2) :: buf
  checks = 0
  buf = '##'
  write(buf,'(SS,I1,I1)') 4,5
  if (len(buf) /= 2) then
    write(*,'(a)') 'F132134:one_data_descriptor_per_item:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '45') then
    write(*,'(a)') 'F132134:one_data_descriptor_per_item:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:one_data_descriptor_per_item:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 ONE_DATA_DESCRIPTOR_PER_ITEM OK'
end program f132134_one_data_descriptor_per_item
