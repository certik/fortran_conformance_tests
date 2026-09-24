! rule: S14.2.2-002
! covers: use-accesses-named-data-object use-accesses-nonintrinsic-type use-accesses-procedure use-accesses-generic-identifier use-accesses-namelist-group use-associated-entity-identity use-associated-attributes-preserved use-associated-variable-previously-declared use-associated-nonvariable-previously-defined
! evidence: effect
! standard: f2023
! oracle-basis: standard
module s1422_002_wrong_type_provider
  implicit none
  type :: box
    integer :: payload = -12
  end type
end module
module s1422_002_provider
  implicit none
  integer :: data_value = 11
  integer :: shared = 5
  integer, parameter :: width = 3
  integer :: nl_value = -777
  integer :: nl_shadow = -888
  namelist /provider_group/ nl_value
  abstract interface
    integer function abstract_answer()
    end function
  end interface
  type :: box
    integer :: payload = 12
  end type
  interface generic_value
    module procedure generic_int, generic_real
  end interface
contains
  integer function answer()
    answer = 23
  end function
  integer function generic_int(arg)
    integer, intent(in) :: arg
    generic_int = 31 + arg - arg
  end function
  integer function generic_real(arg)
    real, intent(in) :: arg
    generic_real = 32 + int(arg) - int(arg)
  end function
end module
program use_assoc_entity_kinds
  use s1422_002_provider, only: data_value, box, answer, abstract_answer, generic_value, &
       provider_group, nl_value, a => shared, b => shared, width
  implicit none
  integer :: checks, observed, bounds_array(width)
  character(len=48) :: nml_input
  procedure(abstract_answer), pointer :: proc
  type(box) :: item
  checks = 0
  observed = -777
  observed = data_value
  if (observed /= 11) error stop 1
  checks = checks + 1
  item = box()
  if (item%payload /= 12) error stop 2
  checks = checks + 1
  proc => local_abstract_answer
  if (proc() /= 70) error stop 3
  checks = checks + 1
  if (answer() /= 23) error stop 4
  checks = checks + 1
  if (generic_value(3) /= 31) error stop 5
  checks = checks + 1
  if (generic_value(2.0) /= 32) error stop 6
  checks = checks + 1
  if (nl_value /= -777) error stop 7
  checks = checks + 1
  nml_input = '&provider_group nl_value=64 /'
  read(nml_input, nml=provider_group)
  if (nl_value /= 64) error stop 8
  checks = checks + 1
  a = 41
  if (b /= 41) error stop 9
  checks = checks + 1
  if (size(bounds_array) /= 3) error stop 10
  checks = checks + 1
  b = 52
  if (a /= 52) error stop 11
  checks = checks + 1
  item = box(answer())
  if (item%payload /= 23) error stop 12
  checks = checks + 1
  if (checks /= 12) error stop 13
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 ENTITY KINDS OK'
contains
  integer function local_abstract_answer()
    local_abstract_answer = 70
  end function
  integer function wrong_abstract_answer()
    wrong_abstract_answer = -70
  end function
end program
