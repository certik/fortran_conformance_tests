! rule: S19.5.1.3-001
! covers: use-stmt-name-association use-renaming-cross-reference use-associated-access-throughout-execution
! evidence: effect
! standard: f2023
! oracle-basis: standard
module association_use_provider
  implicit none
  integer :: shared = 41
  integer :: wrong_shared = 91
end module association_use_provider
program association_use_persistence
  use association_use_provider, only: alias => shared, wrong_shared
  implicit none
  integer :: shared, first_seen, later_seen, checks
  shared = 501
  first_seen = -11
  later_seen = -12
  checks = 0
  call read_imported()
  call mutate_imported()
  call read_later()
  call expect_equal(first_seen, 41, 'use associated original value')
  call expect_equal(alias, 77, 'renamed use association after write')
  call expect_equal(later_seen, 77, 'use association persists through execution')
  call expect_equal(shared, 501, 'local wrong-resolution sentinel')
  call expect_equal(checks, 4, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 USE PERSISTENCE OK'
contains
  subroutine read_imported()
    implicit none
    first_seen = alias
  end subroutine read_imported
  subroutine mutate_imported()
    implicit none
    alias = 77
  end subroutine mutate_imported
  subroutine read_later()
    implicit none
    later_seen = alias
  end subroutine read_later
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_use_persistence
