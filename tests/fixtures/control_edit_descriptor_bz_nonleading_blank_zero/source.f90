! rule: S13.8.7-001
! covers: BZ-sets-zero
! Expected characters and numeric values are hand-derived from Fortran 2023 clause 13.
program ced_bz_nonleading_blank_zero
  implicit none
  integer :: checks
  character(len=3) :: input
  integer :: observed
  checks=0
  input = '1 2'; observed = -999
  read(input,'(BZ,I3)') observed
  if (observed /= 102) then
    write(*,'(a)') 'CED:bz_nonleading_blank_zero:observed-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'CED:bz_nonleading_blank_zero:check-total'
    error stop
  end if
  write(*,'(a)') 'CONTROL EDIT BZ_NONLEADING_BLANK_ZERO OK'
end program ced_bz_nonleading_blank_zero
