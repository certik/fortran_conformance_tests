! rule: S14.2.2-012
! covers: use-associated-different-accessibility-permitted use-associated-asynchronous-permitted use-associated-volatile-permitted
! evidence: effect
! standard: f2023
! oracle-basis: standard
module s1422_012_provider
  implicit none
  integer :: shared = 42
end module
module s1422_012_attr_provider
  implicit none
  integer :: attr_shared = 42
end module
module s1422_012_reexporter
  use s1422_012_provider, only: shared
  implicit none
  private :: shared
  public :: read_shared
contains
  integer function read_shared()
    read_shared = shared
  end function
end module
program use_assoc_attribute_exceptions
  implicit none
  integer :: checks
  checks = 0
  call check_private(checks)
  call check_async(checks)
  call check_volatile(checks)
  if (checks /= 3) error stop 4
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 ATTRIBUTE EXCEPTIONS OK'
contains
  subroutine check_private(checks)
    use s1422_012_reexporter, only: read_shared
    implicit none
    integer, intent(inout) :: checks
    if (read_shared() /= 42) error stop 1
    checks = checks + 1
  end subroutine
  subroutine check_async(checks)
    use s1422_012_attr_provider, only: async_shared => attr_shared
    implicit none
    asynchronous :: async_shared
    integer, intent(inout) :: checks
    if (async_shared /= 42) error stop 2
    checks = checks + 1
  end subroutine
  subroutine check_volatile(checks)
    use s1422_012_attr_provider, only: vol_shared => attr_shared
    implicit none
    volatile :: vol_shared
    integer, intent(inout) :: checks
    if (vol_shared /= 42) error stop 3
    checks = checks + 1
  end subroutine
end program
