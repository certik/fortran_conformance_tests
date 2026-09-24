! rule: S14.2.2-013
! covers: multiple-use-same-module-permitted
! evidence: effect
! standard: f2023
! oracle-basis: standard
module same_module_provider
  implicit none
  integer :: answer = 42
  integer :: bonus = 41
end module
program multiple_use_same_module
  use same_module_provider, only: a => answer
  use same_module_provider, only: b => bonus
  implicit none
  if (a + b /= 83) error stop 1
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 MULTIPLE USE SAME MODULE OK'
end program
