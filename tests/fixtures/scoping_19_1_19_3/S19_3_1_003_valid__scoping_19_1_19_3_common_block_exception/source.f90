! rule: S19.3.1-003
! covers: common-block-name-exception
! evidence: effect
! standard: f2023
! oracle-basis: standard
program scoping_common_block_exception
  implicit none
  integer :: cb_member
  common /blk/ cb_member
  integer :: blk, checks
  cb_member = 29
  blk = 17
  checks = 0
  call expect_equal(blk, 17, 'local blk ordinary occurrence')
  call expect_equal(cb_member, 29, 'common block storage')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 COMMON BLOCK EXCEPTION OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_common_block_exception
