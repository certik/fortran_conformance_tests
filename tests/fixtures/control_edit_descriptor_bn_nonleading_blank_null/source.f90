! rule: S13.8.7-001
! covers: BN-sets-null
! Expected characters and numeric values are hand-derived from Fortran 2023 clause 13.
program ced_bn_nonleading_blank_null
  implicit none
  integer :: checks
  character(len=3) :: input
  integer :: observed
  checks=0
  input = '1 2'; observed = -999
  read(input,'(BN,I3)') observed
  if (observed /= 12) then
    write(*,'(a)') 'CED:bn_nonleading_blank_null:observed-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'CED:bn_nonleading_blank_null:check-total'
    error stop
  end if
  write(*,'(a)') 'CONTROL EDIT BN_NONLEADING_BLANK_NULL OK'
end program ced_bn_nonleading_blank_null
