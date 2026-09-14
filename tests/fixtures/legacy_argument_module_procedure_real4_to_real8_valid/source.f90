module s15524_m
    implicit none
contains
    subroutine t(x)
        real(8), intent(in) :: x
    end subroutine
end module
subroutine s15524_module_procedure()
    use s15524_m
    implicit none
    call t(1.0_8)
end subroutine
