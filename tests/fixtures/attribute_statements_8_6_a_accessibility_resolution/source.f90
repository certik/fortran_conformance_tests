module attribute_8_6_a_checks
implicit none
integer :: checked = 0
contains
subroutine check_int(label, actual, expected)
character(*), intent(in) :: label
integer, intent(in) :: actual, expected
if (actual /= expected) then
  print *, 'CHECK_INT', trim(label), actual, expected
  error stop 1
end if
checked = checked + 1
end subroutine
subroutine check_true(label, actual)
character(*), intent(in) :: label
logical, intent(in) :: actual
if (.not. actual) then
  print *, 'CHECK_TRUE', trim(label)
  error stop 2
end if
checked = checked + 1
end subroutine
subroutine finish_checks(expected)
integer, intent(in) :: expected
if (checked /= expected) then
  print *, 'CHECK_COUNT', checked, expected
  error stop 3
end if
print '(a)', 'ATTRIBUTE STATEMENTS 8.6.A OK'
end subroutine
end module attribute_8_6_a_checks
module a861_provider
        implicit none
        private
        integer, parameter :: pconst = 17
        integer :: var_public = 23
        type :: t_public
          integer :: n = 37
        end type t_public
        interface gen
          module procedure gen_i
        end interface
        interface operator(+)
          module procedure add_t
        end interface
        interface assignment(=)
          module procedure assign_t
        end interface
        public :: pconst, var_public, proc_public, t_public, gen, operator(+), assignment(=)
        contains
        integer function proc_public()
        proc_public = 41
        end function proc_public
        integer function gen_i(x)
integer, intent(in) :: x
        gen_i = x + 5
        end function gen_i
        function add_t(a, b) result(r)
type(t_public), intent(in) :: a, b
type(t_public) :: r
        r%n = a%n + b%n + 1
        end function add_t
        subroutine assign_t(lhs, rhs)
type(t_public), intent(out) :: lhs
integer, intent(in) :: rhs
        lhs%n = rhs + 2
        end subroutine assign_t
        end module a861_provider
        module a861_receiver
        use a861_provider
        implicit none
        private
        integer, parameter :: local_public = 43
        integer :: local_private = 47
        public :: pconst, var_public, proc_public, t_public, gen, operator(+), assignment(=)
        public :: local_public
        private :: local_private
        contains
        integer function receiver_private_value()
        receiver_private_value = local_private
        end function receiver_private_value
        end module a861_receiver
        module a861_fallbacks
        use a861_provider, only: t_public
        implicit none
        private
        interface gen
          module procedure fallback_gen
        end interface
        interface operator(+)
          module procedure fallback_add_t
        end interface
        interface assignment(=)
          module procedure fallback_assign_t
        end interface
        public :: gen, operator(+), assignment(=)
        contains
        integer function fallback_gen(x)
        integer, intent(in) :: x
        fallback_gen = x + 105
        end function fallback_gen
        function fallback_add_t(a, b) result(r)
        type(t_public), intent(in) :: a, b
        type(t_public) :: r
        r%n = a%n + b%n + 101
        end function fallback_add_t
        subroutine fallback_assign_t(lhs, rhs)
        type(t_public), intent(out) :: lhs
        integer, intent(in) :: rhs
        lhs%n = rhs + 102
        end subroutine fallback_assign_t
        end module a861_fallbacks
        program p
        use attribute_8_6_a_checks
        use a861_receiver
        implicit none
        type(t_public) :: assigned, left, right, summed, default_obj
        left%n = 2
        right%n = 3
        assigned = 5
        summed = left + right
        call check_int('access-named-constant', pconst, 17)
        call check_int('access-variable-name', var_public, 23)
        call check_int('access-procedure-name', proc_public(), 41)
        call check_int('access-generic-name', gen(3), 8)
        call check_int('access-assignment-generic', assigned%n, 7)
        call check_int('access-operator-generic', summed%n, 6)
        call check_int('access-nonintrinsic-type', default_obj%n, 37)
        call check_int('access-local-public', local_public, 43)
        call finish_checks(8)
end program p
